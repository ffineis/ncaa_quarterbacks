import argparse
import pickle as pkl
import pandas as pd
import numpy as np
import sqlalchemy as sa
import mysql_helpers as sql
from fuzzywuzzy import fuzz


# --------------------------------------------------- #
# command line argument parser, example usage:
# $ python run_load.py -u ffineis -p password -i ./cfbstats_122017.pkl
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
parser.add_argument('-i'
                    , '--input'
                    , default=None
                    , type=str
                    , help='input filepath to team metadata .pkl file containing'\
                           ' results of scrapers/run_scrape.py')
args = parser.parse_args()
parser.parse_args()


def misspelled_hometown(town_a, town_b, threshold=0.8):
    """
    It's likely that thousands of players have their hometowns misspelled, so this function attempts to
    reduce the number of duplicate players that exist because they come from misspelled hometowns,
    e.g. "Downingtown, PA" and "Downing Town, PA" or "Shippensville, PA" and "Shippenville, PA"
    (Shippensville, PA does not exist)

    Note: I'll assume that there aren't two players with exactly the same name coming from the same hometown,
    which is a modest assumption, but still an assumption (e.g. there are 15 Christopher Jacobses)
    """
    if fuzz.ratio(town_a, town_b) > threshold or fuzz.partial_token_set_ratio(town_a, town_b) > threshold:
        return True
    else:
        return False


if __name__ == '__main__':

    # Required overhead: connect to college_football db and obtain the names
    # of individual player statistics fields
    eng_str = 'mysql+mysqlconnector://' + args.user + ':' + args.password + '@' + args.host + '/college_football'
    eng = sa.engine.create_engine(eng_str)

    # ---------------------------------------------------- #
    # Read in results of run_scrape.py cfbstats.com scrape #
    # ---------------------------------------------------- #
    with open(args.input, 'rb') as f:
        dat = pkl.load(f)

    # ------------------------- #
    # Load in low-hanging fruit #
    # ------------------------- #
    print('Loading conference table.')
    out = sql.insert(dat['conference']
                     , engine=eng
                     , table='conference'
                     , id_fields=['conference_name']
                     , verbose=True)

    print('Loading team table.')
    out = sql.insert(dat['team']
                     , engine=eng
                     , table='team'
                     , id_fields=['team_name']
                     , verbose=True)

    print('Loading positions table.')
    out = sql.insert(dat['positions']
                     , engine=eng
                     , table='positions'
                     , id_fields=['position_name']
                     , verbose=True)

    print('Loading conference_team table.')
    conf_df = pd.read_sql(con=eng
                          , sql='SELECT * FROM conference;')
    team_df = pd.read_sql(con=eng
                          , sql='SELECT * FROM team;')
    conf_team_df = dat['conference_team'].merge(conf_df, on='conference_name').merge(team_df, on='team_name')
    out = sql.insert(conf_team_df
                     , engine=eng
                     , table='conference_team'
                     , id_fields=['conference_id', 'team_id']
                     , verbose=True)

    # -------------------------------------------------------------- #
    # Clean up and format set of players to have played college ball #
    # -------------------------------------------------------------- #
    print('Cleaning up set of individual college football players.')
    player_df_list = list()
    player_dat = dat['player_year_dict']
    for yr in player_dat:
        for team in player_dat[yr]:
            player_df = player_dat[yr][team][['player_hometown', 'name']]
            player_df = player_df.rename(index=int
                                         , columns={'name': 'player_name'})
            player_df_list.append(player_df)

    # Drop players when name, position, team are repeated
    # (because hometown, height, weight, etc tend to change over time (data not perfect))
    player_df = pd.concat(player_df_list
                          , ignore_index=True)
    player_df.drop_duplicates(['player_name', 'player_hometown'], inplace=True)
    player_df.drop_duplicates(['player_name', 'team', 'position'], inplace=True)

    # Reduce number of duplicated players due to hometown misspelling
    repeated_players = player_df['player_name'].value_counts()[
        player_df['player_name'].value_counts() == 2].index.tolist()
    repeated_players_df = player_df[player_df['player_name'].isin(repeated_players)]

    drop_idx = list()
    for player_name in repeated_players_df['player_name'].unique():
        repeat_player_df = repeated_players_df[repeated_players_df['player_name'] == player_name]
        towns = repeated_players_df['player_hometown'].tolist()
        likely_duplicate = misspelled_hometown(towns[0], towns[1])
        if likely_duplicate:
            drop_idx.append(repeat_player_df.index[1])

    print('Dropping %d players due to likely duplicates from misspelled player hometowns' % len(drop_idx))
    player_df.drop(drop_idx
                   , inplace=True)

    # --------------------------- #
    # Load data into player table #
    # --------------------------- #
    print('Loading player table')
    out = sql.insert(player_df
                     , engine=eng
                     , table='player'
                     , id_fields=['player_name']
                     , verbose=True)

    # ------------------------------------------------------------------------------------ #
    # Format temporal player <> position <> team relationships (who played what for whom)  #
    # Format player statistics
    # ------------------------------------------------------------------------------------ #
    print('Finding who played what for whom, and how each player played.')
    player_pos_df_list = list()
    player_stat_df_list = list()
    player_pos_fields = ['height', 'weight', 'year_in_school', 'position_name', 'player_name', 'player_hometown']
    player_stat_fields = list(sql.get_mysql_table_schema(eng, 'player_stats').keys())
    player_dat = dat['player_year_dict']
    for yr in player_dat:
        for team in player_dat[yr]:
            player_df = player_dat[yr][team]
            player_df = player_df.rename(index=int
                                         , columns={'position': 'position_name'
                                                    , 'name': 'player_name'})

            # acquire data for team_player_position table
            player_pos_df = player_df[list(set(player_df.columns).intersection(set(player_pos_fields)))]
            player_pos_df['year'] = yr
            player_pos_df['team_name'] = team
            player_pos_df_list.append(player_pos_df)

            # acquire data for player_statistics table
            player_stat_df = player_df[list(set(player_stat_fields).intersection(set(player_df.columns)))
                                       + ['player_name', 'player_hometown']]
            player_stat_df['year'] = yr

            # Drop players with no meaningful statistics
            player_stat_cols = list(set(player_stat_df.columns)
                                    - set(['player_id', 'year', 'player_hometown', 'player_name']))
            tmp_df = player_stat_df[player_stat_cols]
            tmp_df = tmp_df.where((pd.notnull(tmp_df)), np.NaN)
            tmp_df.dropna(axis=0, how='all', inplace=True)
            player_stat_df = player_stat_df.loc[tmp_df.index]
            player_stat_df_list.append(player_stat_df.where((pd.notnull(player_stat_df)), None))

    player_pos_df = pd.concat(player_pos_df_list
                              , ignore_index=True).drop_duplicates()
    del player_pos_df_list
    player_stat_df = pd.concat(player_stat_df_list
                              , ignore_index=True).drop_duplicates()
    del player_stat_df_list

    # Get primary keys required to establish relationships: team_id, player_id, position_id
    position_df = pd.read_sql(con=eng
                              , sql='SELECT * FROM positions;')
    players_df = pd.read_sql(con=eng
                             , sql='SELECT * FROM player;')

    player_pos_df = player_pos_df.merge(team_df, on='team_name')\
        .merge(position_df, on='position_name')\
        .merge(players_df, on=['player_name', 'player_hometown'])

    player_stat_df = player_stat_df.merge(players_df, on=['player_name', 'player_hometown'])

    # ----------------------------------------------------------- #
    # Load data into team_player_position and player_stats tables #
    # ----------------------------------------------------------- #
    print('Loading team_player_position table.')
    out = sql.insert(player_pos_df
                     , engine=eng
                     , table='team_player_position'
                     , id_fields=['team_id', 'position_id', 'player_id', 'year']
                     , verbose=True)

    print('Loading player_stats table.')
    out = sql.insert(player_stat_df
                     , engine=eng
                     , table='player_stats'
                     , id_fields=['player_id', 'year']
                     , verbose=True)

    print('Successfully uploaded cfbstats.com data into college_football database!')