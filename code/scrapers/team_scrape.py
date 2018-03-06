from bs4 import BeautifulSoup
import requests
import os
from json import dump
from conference_scrape import get_conference_metadata

# TODO: consider parallelizing get_team_metadata
# TODO: check if output_file is writable location
def get_team_metadata(output_file=None):
    """
    Get year, conference, team relations from cfbstats.com

    :param output_file: full output file path to dump team scrape into a .json, default None
    means don't save output

    :return: nested dictionary with years as keys, then dictionary
    of conference, dictionary of team: URL's, wins, losses
    """
    base_url = 'http://www.cfbstats.com/%d/team/index.html'
    conf_team_dict = dict()

    conferences = get_conference_metadata()
    yrs = list(conferences.keys())

    for yr in yrs:
        r = requests.get(base_url % yr)

        if r.status_code != 200:
            raise Warning('Error in querying conference<>team data for %d. Skipping.' % yr)
            next

        conf_team_dict[yr] = dict()
        soup = BeautifulSoup(r.text, 'html.parser')
        confs = soup.find_all('div', {'class', 'conference'})

        # Iterate over conferences available in the year
        for conf in confs:
            conf_name = conf.find('h1').text
            teams = conf.find_all('a')
            conf_team_dict[yr][conf_name] = dict()

            # Iterate over teams in the conference for a year
            for team in teams:
                # Collect team name and URL for index page and team roster
                team_name = team.text
                index_url = 'http://www.cfbstats.com%s' % team['href']
                roster_url = index_url.replace('index', 'roster')
                conf_team_dict[yr][conf_name][team_name] = dict()
                conf_team_dict[yr][conf_name][team_name]['index_url'] = index_url
                conf_team_dict[yr][conf_name][team_name]['roster_url'] = roster_url

                # Hit the index page and get the win/loss record for each valid conference/team/year 3-tuple
                r2 = requests.get(index_url)
                soup2 = BeautifulSoup(r2.text, 'html.parser')
                wl = soup2.find('div', {'class': 'team-record'}).find_all('td')[1].text.split('-')
                conf_team_dict[yr][conf_name][team_name]['wins'] = int(wl[0])
                conf_team_dict[yr][conf_name][team_name]['losses'] = int(wl[1])

    # Dump output, if desired.
    if output_file:
        with open(output_file, 'w') as of:
            dump(conf_team_dict, fp=of, ensure_ascii=True)

    return(conf_team_dict)


if __name__ == '__main__':
    print('Saving College football teams by conference, by year.')
    print(get_team_metadata(os.path.join(os.getenv('HOME'), 'Desktop', 'team_metadata.txt')))
    print('Finished!')