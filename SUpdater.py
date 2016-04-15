import gspread
from oauth2client.service_account import ServiceAccountCredentials
import urllib.request as ur
from bs4 import BeautifulSoup
import re


series_name = 0
series_watched = 1
series_last = 2
series_url = 3

scope = ["https://spreadsheets.google.com/feeds"]

credential = ServiceAccountCredentials.from_json_keyfile_name('SeriesUpdater-4c3e977fa468.json', scope)

gs = gspread.authorize(credential)

wks = gs.open("WTF").sheet1


def get_series_list():
    series_list = wks.get_all_values()[1:]
    return series_list


def check_new_series(series_list):
    new_series = []
    for series in series_list:
        if not(series[series_url] == ''):
            if series[series_url].find('lostfilm') != -1:
                last_series = lostfilm_update(series[series_url])
            elif series[series_url].find('filiza') != -1:
                last_series = filiza_update(series[series_url])
            elif series[series_url].find('vo-production') != -1:
                last_series = vo_production_update(series[series_url])
            elif series[series_url].find('anidub') != -1:
                last_series = anidub_update(series[series_url])
            else:
                last_series = [1, 1]
            last_known_series = series[series_last].split(',')
            if not (last_series[0] > last_known_series[0]):
                if last_series[0] == last_known_series[0] and last_series[1] > last_known_series[1]:
                    series[series_last] = last_series[0] + ',' + last_series[1]
                    new_series.append(series)
            else:
                series[series_last] = last_series[0] + ',' + last_series[1]
                new_series.append(series)
    return new_series


def update_series_list(new_series):
    for series in new_series:
        row = wks.find(series[series_name]).row
        wks.update_cell(row, series_last + 1, series[series_last])


def lostfilm_update(url):
    req = ur.Request(url, headers={'User-Agent': "Magic Browser"})
    response = ur.urlopen(req)
    html = response
    soup = BeautifulSoup(html, 'html.parser')
    m = re.search("(?<=ShowAllReleases)\(\S*\)", str(soup))
    m = m.group(0).split(',')[1:]
    last_series = []
    for temp in m:
        last_series.append(re.search('[1-9]+\d*', temp).group(0))
    return last_series


def filiza_update(url):
    req = ur.Request(url, headers={'User-Agent': "Magic Browser"})
    response = ur.urlopen(req)
    html = response
    soup = BeautifulSoup(html, 'html.parser')
    serial = re.search('/serial-\S+[^/]+', url).group(0)
    m = re.search("(?<=" + serial + "\?s=)\d+\S+\d+", str(soup))
    m = m.group(0).split(';')
    last_series = []
    for temp in m:
        last_series.append(re.search('[1-9]+\d*', temp).group(0))
    return last_series


def vo_production_update(url):
    req = ur.Request(url, headers={'User-Agent': "Magic Browser"})
    response = ur.urlopen(req)
    html = response
    soup = BeautifulSoup(html, 'html.parser')
    season_number = re.search('/Sezon\d+', str(soup)).group(0)
    req = ur.Request(url + season_number, headers={'User-Agent': "Magic Browser"})
    response = ur.urlopen(req)
    html = response
    soup = BeautifulSoup(html, 'html.parser')
    m = re.findall("(?<=Сезон )\d+ Серия \d+", str(soup))
    m = m[len(m) - 1].split('Серия')
    last_series = []
    for temp in m:
        last_series.append(re.search('[1-9]+\d*', temp).group(0))
    return last_series


def anidub_update(url):
    req = ur.Request(url, headers={'User-Agent': "Magic Browser"})
    response = ur.urlopen(req)
    html = response
    soup = BeautifulSoup(html, 'html.parser')
    m = re.search("\d+ из \d+", str(soup))
    m = m.group(0).split(" из ")[:1]
    last_series = ['1']
    for temp in m:
        last_series.append(re.search('[1-9]+\d*', temp).group(0))
    return last_series


def do_it():
    series_list = get_series_list()
    new_series = check_new_series(series_list)
    update_series_list(new_series)
do_it()
