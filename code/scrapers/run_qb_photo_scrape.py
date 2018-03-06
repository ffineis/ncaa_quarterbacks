import urllib
import requests
import shutil
import argparse
import pandas as pd
import os
from bs4 import BeautifulSoup


def get_google_image_urls(query_str, n_imgs=3):
    """
    Get top n image URLs of result of a google image search

    :param query_str: query you want to enter into google image search bar
    :param n_imgs: number of top image urls to return
    :return:
    """
    base = 'http://www.google.com/search?'
    query_vars= {'q': query_str, 'tbm': 'isch'}
    google_resp = requests.get(base, params=query_vars)

    if google_resp.status_code != 200:
        print(google_resp.status_code)
        raise requests.exceptions.RequestException('Google Image GET request failed!')

    google_soup = BeautifulSoup(google_resp.text
                                , 'html.parser')
    img_tags = google_soup.find_all('img')

    if len(img_tags) == 0:
        raise UserWarning('No images were found with query string %s' % query_str)

    img_urls = list(map(lambda x: x['src'], img_tags))[:min(n_imgs, len(img_tags)-1)]
    return(img_urls)


def download_jpeg(url, output_file):
    with urllib.request.urlopen(url) as response, open(output_file, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i'
                        , '--input'
                        , type=str
                        , default=os.path.join(os.path.dirname(os.path.realpath(__file__))
                                               , '../../data/quarterbacks.tsv')
                        , help='path to input quarterback TSV data file (see SQL queries)')
    parser.add_argument('-o'
                        , '--output'
                        , type=str
                        , default=os.path.join(os.path.dirname(os.path.realpath(__file__))
                                               , '../../data/qb_images')
                        , help='path to output directory where quarterback images will be downloaded')
    parser.add_argument('-n'
                        , '--n_imgs_per_player'
                        , type=int
                        , default=3
                        , help='number of images to download per player')
    args = parser.parse_args()
    parser.parse_args()

    print('Loading in quarterback information from %s' % args.input)
    qb_df = pd.read_table(args.input)
    n_qbs = qb_df.shape[0]

    if not os.path.isdir(args.output):
        print('%s directory not found. Creating it now.' % args.output)
        os.mkdir(args.output)

    for i in range(n_qbs):
        qb_name = qb_df['player_name'][i].split(', ')
        first_name = qb_name[1]
        last_name = qb_name[0]
        qb_team = qb_df['team_name'][i]

        if i % 20 == 0:
            print('Downloading images of quarterback %s %s  --  (%d/%d)' % (first_name, last_name, i, n_qbs))

        query_str = (first_name + ' '+ last_name + ' quarterback ' + qb_team)
        urls = get_google_image_urls(query_str
                                     , n_imgs=args.n_imgs_per_player)
        for ii in range(len(urls)):
            download_jpeg(urls[ii]
                          , output_file=os.path.join(args.output, '%s_%s_%s_%d.jpeg' %
                                                     (last_name, first_name, qb_team, ii)))