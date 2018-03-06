from bs4 import BeautifulSoup
import requests
from scrape_params import get_player_stat_mapping, standardize_field_name


def get_players_from_roster(roster_url):
    """
    Get players and certain player metadata from a team roster URL
    on cfbstats.com

    :param roster_url: URL to a team roster, e.g.
    http://www.cfbstats.com/2015/team/128/roster.html
    :return: list of dictionaries, one dictionary per player, contains
    player-specific info like name, number, height, player URL
    """
    r = requests.get(roster_url)
    if r.status_code != 200:
        raise Warning('Error in querying roster URL %s.' % roster_url)

    soup = BeautifulSoup(r.text, 'html.parser')
    roster = soup.find('div', {'class', 'team-roster'})
    player_list = list()

    player_urls = roster.find_all('a')
    player_urls_player_names = list(map(lambda x: x.text, player_urls))
    player_urls = list(map(lambda x: 'http://www.cfbstats.com/' + x['href'], player_urls))
    player_url_dict = dict(zip(player_urls_player_names, player_urls))

    players = roster.find_all('tr')
    player_fields = ['number', 'name', 'position', 'year_in_school',
                     'height', 'weight', 'hometown', 'last_school']
    integer_fields = ['number', 'weight']
    players = players[1:]

    for player in players:
        player_dat = list(filter(lambda x: x not in [''], player.text.split('\n')))
        player_dict = dict(zip(player_fields, player_dat))

        for field in integer_fields:
            try:
                player_dict[field] = int(player_dict[field])
            except ValueError:
                player_dict[field] = None

        player_dict['url'] = None
        if player_dict['name'] in player_url_dict:
            player_dict['url'] = player_url_dict[player_dict['name']]

        player_list.append(player_dict)

    return(player_list)


def get_player_stats(player_url):
    """
    Get detailed player statistics for a particular year from
    cfbstats.com

    :param player_url: URL to a specific player in a specific year, e.g.
    http://www.cfbstats.com/2015/player/128/1074005/index.html
    :return: dictionary with player performance numbers
    """
    r = requests.get(player_url)
    if r.status_code != 200:
        raise Warning('Error in querying player URL %s.' % player_url)

    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.find_all('table')
    player_stats = dict()
    field_mapping = get_player_stat_mapping()

    for table in tables:
        table_name = standardize_field_name(table.caption.text)
        table_fields = list(map(lambda x: standardize_field_name(x.text), table.find_all('th')))
        table_values = list(map(lambda x: x.text, table.find_all('td')))

        for i in range(len(table_values)):
            try:
                table_values[i] = int(table_values[i])
            except ValueError:
                table_values[i] = None

            field = table_name + '_' + field_mapping.get(table_fields[i], table_fields[i])
            table_fields[i] = field

        player_stats.update(dict(zip(table_fields, table_values)))

    return(player_stats)


if __name__ == '__main__':
    print('Scraping sample team roster:')
    print(get_players_from_roster('http://www.cfbstats.com/2016/team/716/roster.html'))

    print('Scraping sample player statistics:')
    print(get_player_stats('http://www.cfbstats.com//2016/player/716/1057822/index.html'))

    # # Compile comprehensive set of player statistic fields
    # roster = get_players_from_roster('http://www.cfbstats.com/2016/team/716/roster.html')
    #
    # urls = []
    # for player in roster:
    #     url = player.get('url', None)
    #     if url:
    #         urls.append(url)
    #
    # fields = []
    # for url in urls:
    #     fields += list(get_player_stats(url).keys())
    #
    # print('\n'.join(sorted(list(set(fields)))))