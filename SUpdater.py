import gspread
from oauth2client.service_account import ServiceAccountCredentials
import urllib.request as ur
from bs4 import BeautifulSoup
import re
from multiprocessing.dummy import Pool


series_name = 0
series_watched = 1
series_last = 2
series_url = 3
series_state = 4
number_of_pool = 9

pool = Pool(number_of_pool)

proxy = ur.ProxyHandler(
    {
        'https': 'https://158.69.237.1:3128',
        'http': 'http://107.151.152.218:80'
    }
)
opener = ur.build_opener(proxy)

scope = ["https://spreadsheets.google.com/feeds"]

credential = ServiceAccountCredentials.from_json_keyfile_name('SeriesUpdater-4c3e977fa468.json', scope)

gs = gspread.authorize(credential)

wks = gs.open("WTF").sheet1


def get_series_list():
    series_list = wks.get_all_values()[1:]
    return series_list


def check_new_series(series):
    new_series = None
    if not(series[series_url] == ''):
        if series[series_url].find('lostfilm') != -1:
            last_series = lostfilm_update(series[series_url])
        elif series[series_url].find('filiza') != -1:
            last_series = filiza_update(series[series_url])
        elif series[series_url].find('vo-production') != -1:
            last_series = vo_production_update(series[series_url])
        elif series[series_url].find('anidub') != -1:
            if series[series_state] != 'сезон просмотрен':
                last_series = anidub_update(series[series_url])
                if(last_series[1] == last_series[2]) and (last_series[1] == series[series_watched].split('\\')[1]):
                    series[series_state] = 'сезон просмотрен'
                    update_series_state(series)
                last_series = last_series[:-1]
            else:
                last_series = series[series_watched].split('\\')
        else:
            last_series = [0, 0]
        if series[series_last] == '':
            last_known_series = [0, 0]
        else:
            last_known_series = series[series_last].split('\\')
        print(last_series, last_known_series)
        if not (int(last_series[0]) > int(last_known_series[0])):
            if int(last_series[0]) == int(last_known_series[0]) and int(last_series[1]) > int(last_known_series[1]):
                series[series_last] = last_series[0] + '\\' + last_series[1]
                new_series = series
        else:
            series[series_last] = last_series[0] + '\\' + last_series[1]
            new_series = series
    return new_series


def check_new_series_list(series_list):
    new_series = []
    temp = pool.map(check_new_series, series_list)
    pool.close()
    pool.join()
    for series in temp:
        if series:
            new_series.append(series)
    return new_series


def update_series_state(series):
    row = wks.find(series[series_name]).row
    wks.update_cell(row, series_state + 1, series[series_state])


def update_series_list(new_series):
    for series in new_series:
        print(series)
        row = wks.find(series[series_name]).row
        wks.update_cell(row, series_last + 1, series[series_last])


def get_soup(url):
    req = ur.Request(url, headers={'User-Agent': "Magic Browser"})
    try:
        if url.find('lostfilm') != -1:
            response = opener.open(req)
        else:
            response = ur.urlopen(req)
    except (ur.HTTPError, ur.URLError):
        return None
    html = response
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def lostfilm_update(url):
    soup = get_soup(url)
    if not soup:
        return ['0', '0']
    m = re.search("(?<=ShowAllReleases)\(\S*\)", str(soup))
    m = m.group(0).split(',')[1:]
    last_series = []
    for temp in m:
        res = re.search('\d+', temp).group(0)
        if res[0] == '0':
            res = res[1:]
        last_series.append(res)
    return last_series


def filiza_update(url):
    soup = get_soup(url)
    if not soup:
        return ['0', '0']
    serial = re.search('/serial-\S+[^/]+', url).group(0)
    m = re.search("(?<=" + serial + "\?s=)\d+\S+\d+", str(soup))
    m = m.group(0).split(';')
    last_series = []
    for temp in m:
        last_series.append(re.search('[1-9]+\d*', temp).group(0))
    return last_series


def vo_production_update(url):
    soup = get_soup(url)
    if not soup:
        return ['0', '0']
    season_number = re.search('/Sezon\d+', str(soup)).group(0)
    soup = get_soup(url + season_number)
    if not soup:
        return ['0', '0']
    m = re.findall("(?<=Сезон )\d+ Серия \d+", str(soup))
    m = m[len(m) - 1].split('Серия')
    last_series = []
    for temp in m:
        last_series.append(re.search('[1-9]+\d*', temp).group(0))
    return last_series


def anidub_update(url):
    soup = get_soup(url)
    if not soup:
        return ['0', '0', '0']
    m = re.search("\d+ из \d+", str(soup))
    m = m.group(0).split(" из ")
    last_series = ['1']
    for temp in m:
        last_series.append(re.search('[1-9]+\d*', temp).group(0))
    return last_series


def do_it():
    series_list = get_series_list()
    new_series = check_new_series_list(series_list)
    update_series_list(new_series)
do_it()
