import requests
from bs4 import BeautifulSoup as bs4
import os
from os.path import basename
import json
from string import Template
import datetime

MONTHS = {
    'January': 1,
    'February': 2,
    'March': 3,
    'April': 4,
    'May': 5,
    'June': 6,
    'July': 7,
    'August': 8,
    'September': 9,
    'October': 10,
    'November': 11,
    'December': 12
}


def download_cover(album_url):
    album_page = requests.get(album_url)
    soup = bs4(album_page.content, 'html.parser')
    info_table = soup.find(class_='infobox')

    if soup.find(class_='infobox'):
        images = info_table.findAll('img')
        if len(images) > 0:
            image = info_table.findAll('img')[0]
            lnk = 'http:' + image['src']
            # print(lnk)
            with open(os.path.join(os.getcwd() + '/album_covers', basename(lnk)), 'wb') as file1:
                file1.write(requests.get(lnk).content)
            return basename(lnk)
        else:
            return ""
    else:
        return ""


def write_json(data, directory=""):
    with open(directory, 'w') as f:
        json.dump(data, f, indent=4)


def is_a_date(string=""):

    is_valid = True

    string_list = string.split()

    if len(string_list) > 2 or len(string_list) < 2:
        is_valid = False
    elif string_list[0] not in MONTHS:
        is_valid = False
    else:
        try:
            int(string_list[1])
        except ValueError:
            is_valid = False

    return is_valid


def scrape(table=None, URL=None, year=None):
    # print(table)

    date = ""   # date of album
    artist = ""  # artist
    album = ""  # album name
    item = {}   # dictionary to story album data
    totalAlbums = []   # list total album scraped
    album_cover = ""    # album cover name, if available
    prevDateRow = None      # td that contains date

    for tr in table.find_all('tr')[1:]:

        tds = tr.find_all("td")
        # print(tds)

        # print(type(tr))
        # if this row has a date,
        date = tds[0]
        # print(is_a_date(date.text.strip()))
        if is_a_date(date.text.strip()) or date.text.strip().lower() == "unknown":
            prevDateRow = date
        elif date.text.strip() in MONTHS:
            # only has a month, no number
            prevDateRow = date
        else:
            # print(date)
            # this row does not have a date
            tds.insert(0, prevDateRow)
            # pass

        # print(tds)
        more_than_three_col = len(tds) > 3
        while more_than_three_col:
            # print(len(tds))
            tds.pop()
            if len(tds) <= 3:
                # print(len(tds))
                break
            else:
                more_than_three_col = True

        for td in tds:
            ##### Date ######
            if not td.find('a') and not td.find('ul'):
                is_valid_date = is_a_date(td.text.strip())

                if is_valid_date:
                    tmp_date = td.text.strip().split()
                    # print(tmp_date)
                    date = datetime.datetime(
                        int(year), MONTHS[tmp_date[0]], int(tmp_date[1]))
                elif td.text.strip() == "Unknown":  # unknown date
                    # print('#########')
                    # print(td.text.strip())
                    # print('$$$$$$$$$$$$$$$$')
                    date = datetime.datetime(year, 1, 1)
                elif td.text.strip() in MONTHS:  # Only Months
                    # print(td.text)
                    date = datetime.datetime(year, MONTHS[td.text.strip()], 1)

            # artist name
            if td.find("a") and not td.find('i') and not td.find('ul'):
                # print(td.text)
                artist = td.text.strip()
            elif td.find('ul'):  # no notes
                pass
            elif (not is_a_date(td.text.strip())) and td.text.strip().lower() != "unknown" and \
                    td.text.strip().lower() != "april" and not td.find('i'):  # no wiki page for artist

                # print(artist)

                # add wiki to dr.dre
                if td.text.strip() == "Dr. Dre":
                    artist = "Dr. Dre"
                elif td.text.strip() == "":
                    pass
                else:  # some artist that has no wiki page
                    # print(td.text.strip())
                    artist = td.text.strip()
            elif td.find('i'):
                pass

            # album name
            Is = td.find_all('i')
            for _i in Is:
                if _i.find('a'):  # if album has a link
                    album = _i.find('a').get('title')
                    album_cover_url = _i.find('a')['href']
                    album_cover_url = 'https://en.m.wikipedia.org' + \
                        _i.find('a')['href']
                    album_cover = download_cover(album_cover_url)
                elif _i.find('ul'):
                    pass
                else:
                    album = _i.text

        # check for '(page does not exist)'
        if '(page does not exist)' in album:
            new_album = album.replace('(page does not exist)', '')
            album = new_album
        elif '(page does not exist)' in artist:
            new_artist = artist.replace('(page does not exist)', '')
            artist = new_artist

        # print(date)
        item['album'] = album
        item['release_date'] = str(date.year) + "-" + \
            str(date.month) + "-" + str(date.day)
        item['artist'] = artist
        item['album_cover'] = album_cover
        totalAlbums.append(item)
        album = ""
        artist = ""
        album_cover = ""

        print(
            f"Release Date:{item['release_date']}--Artist: {item['artist']}--Album: {item['album']}--Album Cover: {item['album_cover']}")
        item = {}  # reset dictionary

    filename = str(year) + ".json"
    with open(os.path.join(os.getcwd() + '/album_data', filename)) as json_file:
        existing_data = json.load(json_file)

        temp = existing_data['albums']

        for album_item in totalAlbums:
            # python object
            temp.append(album_item)

    directory = os.path.join(os.getcwd() + '/album_data', filename)
    write_json(existing_data, directory)


URLS = []  # our scraping URLs
years = []  # list of years


url_template = Template(
    'https://en.wikipedia.org/wiki/${year}_in_hip_hop_music')

for year in range(1980, 2017):
    s = url_template.substitute(year=year)
    years.append(year)

    URLS.append(s)  # create URLS

# loop through our years to scrape
# albums
for index in range(11, 12):
    print(URLS[index])
    print(years[index])
    page = requests.get(URLS[index])
    soup = bs4(page.content, 'html.parser')

    table = soup.findAll(class_='wikitable')[0]
    # print(table)
    scrape(table, URLS[index], years[index])
