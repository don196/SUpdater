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
            req = ur.Request(series[series_url], headers={'User-Agent': "Magic Browser"})
            response = ur.urlopen(req)
            html = response
            soup = BeautifulSoup(html, 'html.parser')
            m = re.search("(?<=ShowAllReleases)\(\S*\)", str(soup))
            m = m.group(0).split(',')[1:]
            last_series = []
            for temp in m:
                last_series.append(re.search('[1-9]+\d*', temp).group(0))
            last_known_series = series[series_last].split(',')
            if not (last_series[0] > last_known_series[0]):
                if last_series[1] > last_known_series[1]:
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


def do_it():
    series_list = get_series_list()
    new_series = check_new_series(series_list)
    update_series_list(new_series)
do_it()
