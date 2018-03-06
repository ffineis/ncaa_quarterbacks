import re

def get_player_stat_mapping():
    """
    Get mapping between cfbstats.com player statistics terminology
    and a more standardized one used in an RDBMS schema.

    Football terminology learned from https://www.pro-football-reference.com/about/glossary.htm

    :return: dictionary of {cfbstats.com variables: standardized variables}
    """
    stat_map = {
        'g': 'games',
        'tfl': 'tackles_for_loss',
        'tfl_yards': 'tackles_for_loss_yards',
        'att': 'attempts',
        'yards_att': 'yards_attempted',
        'fg': 'field_goals',
        'int': 'interceptions',
        'int_ret': 'interceptions_returned',
        '1xp': 'one_xp',
        '2xp': 'two_xp',
        'rating': 'passer_rating',
        'comp': 'completion',
        'td': 'touchdown'
    }

    return(stat_map)


def standardize_field_name(field_name):
    """
    Standardize the field name of player statistics through string subs/manipluations

    :param field_name: name of a player statistic, e.g. "TFL"
    :return: standardized field_name
    """
    field_name = re.sub(r'[\s\/-\\%]', '_', field_name.lower())
    field_name = re.sub(r'\.', '', field_name)
    return(field_name)