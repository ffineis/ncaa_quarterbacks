from bs4 import BeautifulSoup
import requests
import unicodedata

def get_conference_metadata():
    """
    For the years available, determine the names of the conferences
    available on cfbstats.com

    :return: dictionary of (year, conference name list) pairs
    """
    base_url = 'http://www.cfbstats.com/%d/conference/index.html'
    conf_dict = dict()

    # Determine years that have a conference associated with them.
    r = requests.get(base_url % 2017)
    dat = r.text
    soup = BeautifulSoup(dat, 'html.parser')

    seasons = soup.find(id='seasons').text.split('\n')
    conf_yrs = list(filter(lambda x: unicodedata.normalize('NFKD', x).strip() != '', seasons))

    # Iterate over available years - determine conferences in each year.
    for yr in conf_yrs:
        yr = int(yr)
        r = requests.get(base_url % yr)
        soup = BeautifulSoup(r.text, 'html.parser')

        confs = soup.find(id='conferences').text.split('\n')
        confs = list(filter(lambda x: unicodedata.normalize('NFKD', x).strip() not in ['', 'Conferences']
                            , confs))
        conf_dict[yr] = confs

    return conf_dict


if __name__ == '__main__':
    print('College football conferences, by year:')
    print(get_conference_metadata())
