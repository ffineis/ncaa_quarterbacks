import argparse
import pickle as pkl
import os
import json
import pandas as pd
import sqlalchemy as sa
from team_scrape import get_team_metadata
from player_scrape import get_players_from_roster, get_player_stats
import multiprocessing as mp

# --------------------------------------------------- #
# command line argument parser, example usage:
# $ python run_scrape.py -u ffineis -p password -o ./cfbstats_122017.pkl
# --------------------------------------------------- #

parser = argparse.ArgumentParser()
parser.add_argument('-u'
                    , '--user'
                    , type=str
                    , help='college_football MySQL database username')
parser.add_argument('-p'
                    , '--password'
                    , type=str
                    , help='college_football MySQL database user password')
parser.add_argument('-l'
                    , '--host'
                    , default='localhost'
                    , type=str
                    , help='college_football MySQL database host server address')
parser.add_argument('-t'
                    , '--team_data'
                    , default=None
                    , type=str
                    , help='input filepath to team metadata .txt file, the result of executing '
                           'team_scrape.get_team_metadata, optional')
parser.add_argument('-n'
                    , '--n_jobs'
                    , default=mp.cpu_count() - 1
                    , type=int
                    , help='Number of CPUs to use in parallelized web scrape')
parser.add_argument('-o'
                    , '--output'
                    , default='./cfbstats_scrape.pkl'
                    , help='output filepath for saving the results of the cfb scrape')
args = parser.parse_args()
parser.parse_args()


# Required overhead: connect to college_football db and obtain the names
# of individual player statistics fields
eng_str = 'mysql+mysqlconnector://' + args.user + ':' + args.password + '@' + args.host + '/college_football'
eng = sa.engine.create_engine(eng_str)
conn = eng.connect()
inspector = sa.inspect(eng)
PLAYER_STAT_FIELDS = [x['name'] for x in inspector.get_columns('player_stats')]
conn.close()


def get_player_stats_for_par(team_url_tup):
    """
    For a given college football team name and url,
    get player performance/info data. To be used with multiprocessing.Pool
    methods, e.g. `map`.

    :param team_url_tup: (str team_name , str roster_url) 2-tuple
    :returns: list of {team name, player statistics DataFrame} key-value pairs
    """
    team = team_url_tup[0]
    roster_url = team_url_tup[1]

    player_dfs = list()
    player_dat = get_players_from_roster(roster_url)

    for i in range(len(player_dat)):
        player_info = player_dat[i]
        player_info['name'] = [player_info['name']]

        if player_dat[i]['url']:
            player_stats = None
            while not player_stats:
                try:
                    player_stats = get_player_stats(player_dat[i]['url'])
                except Exception as e:
                    UserWarning(e)
                    print('...retrying')
                    pass

            for field in PLAYER_STAT_FIELDS:
                player_info[field] = [player_stats.get(field, None)]

        player_dfs.append(pd.DataFrame(player_info))

    players_df = pd.concat(player_dfs
                           , ignore_index=True)
    players_df = players_df.where(pd.notnull(players_df)
                                  , None)
    players_df.dropna(axis=1
                      , how='all'
                      , inplace=True)

    return ({team: players_df})


if __name__ == '__main__':

    # -------------------------------------------------------------- #
    # Check if supplied team metadata exists y/n. If not, scrape it. #
    # -------------------------------------------------------------- #

    team_dat_file = args.team_data
    n_jobs = args.n_jobs

    if not team_dat_file or not os.path.isfile(team_dat_file):
        print('Scraping conference/team relationship data...')
        team_dat = get_team_metadata()

    else:
        print('Loading conference/team relationship data...')
        with open(team_dat_file, 'rb') as f:
            team_dat = json.load(f)

    yrs = sorted(list(team_dat.keys()))
    print('%d years\' worth of college football conferences found.\n' % len(yrs))

    # -------------------------------------------------------------------- #
    # Perform main scrape: iterate over years, conferences, teams, players #
    # -------------------------------------------------------------------- #

    player_year_stats = dict()
    conference_team_dfs = list()

    for i in range(len(yrs)):
        yr = yrs[i]
        print('Scraping cfbstats.com data for year %s  --  (year %d/%d):' % (yr, i + 1, len(team_dat)))

        # assemble conferences
        confs = list(team_dat[yr].keys())

        # get ready to store teams' players' stats on a per-year basis
        player_year_stats[yr] = dict()

        for conf in team_dat[yr]:

            # assemble teams/rosters in a conference in a given year
            conf_teams = list(team_dat[yr][conf].keys())
            roster_urls = list()

            for team in conf_teams:

                # arrange team/conference relationships/wins/losses
                l = team_dat[yr][conf][team]['losses']
                w = team_dat[yr][conf][team]['wins']
                conf_team_df = pd.DataFrame({'year': [int(yr)]
                                                , 'conference_name': [conf]
                                                , 'team_name': [team]
                                                , 'games_won': [w]
                                                , 'games_lost': [l]})
                conference_team_dfs.append(conf_team_df)
                roster_urls.append(team_dat[yr][conf][team]['roster_url'])

            # Begin parallel scrape: get players' stats for a set of teams
            print('    ... obtaining player statistics for %d teams in the %s conference' % (len(conf_teams), conf))
            p = mp.Pool(processes=n_jobs)
            roster_dat = p.map(get_player_stats_for_par
                               , iterable=zip(conf_teams, roster_urls))
            p.close()

            # Append parallel scrape to storage dictionary
            for roster in roster_dat:
                player_year_stats[yr].update(roster)

    # ----------------------------------------------------------- #
    # Save DF's with data to be uploaded into college_football DB #
    # ----------------------------------------------------------- #

    # data to populate college_football.conference_team table
    conference_team_df = pd.concat(conference_team_dfs
                                   , ignore_index=True)

    # data to populate college_football.conference table
    conferences = sorted(conference_team_df['conference_name'].unique().tolist())
    conference_df = pd.DataFrame({'conference_name': conferences})

    # data to populate college_football.team table
    teams = sorted(conference_team_df['team_name'].unique().tolist())
    team_df = pd.DataFrame({'team_name': teams})
    print('Found %d teams comprising %d conferences.\n' % (len(teams), len(conferences)))

    # data to populate college_football.positions, college_football.player tables
    positions = list()
    player_dfs = list()
    for yr in player_year_stats:
        for team in player_year_stats[yr]:
            positions += player_year_stats[yr][team]['position'].unique().tolist()
            player_dfs.append(player_year_stats[yr][team][['name', 'hometown']])

    positions = list(set(positions))
    positions_df = pd.DataFrame({'position_name': positions})
    print('Found %d unique player positions.\n' % (len(positions)))

    players_df = pd.concat(player_dfs
                           , ignore_index=True)
    players_df.drop_duplicates(inplace=True)
    players_df.rename(columns={'name': 'player_name'}
                      , inplace=True)
    print('Found %d unique players over %d years.\n' % (players_df.shape[0], len(yrs)))

    # --------- #
    # Save data #
    # --------- #
    save_dat = {'conference': conference_df
                , 'team': team_df
                , 'conference_team': conference_team_df
                , 'positions': positions_df
                , 'player_year_dict': player_year_stats}

    print('Saving data scraped from cfbstats.com to %s\n' % args.output)
    pkl.dump(save_dat, open(args.output, 'wb'))

    print('Successfully scraped cfbstats.com college football data')

