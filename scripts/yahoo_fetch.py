import csv
import os
import requests
import finsymbols as symbols

#Constants
request_url = 'https://app.quotemedia.com/quotetools/getHistoryDownload.csv'
request_params = {
    'startMonth' : '2',
    'startDay' : '25',
    'startYear' : '2010',
    'endMonth' : '2',
    'endDay' : '25',
    'endYear' : '2018',
    'webmasterId' : '501',
    'symbol' : 'SPY'
}

basePath = "../data/raw/yahoo/S&P500/"

#download ticker data
SP500ticker = list(i['symbol'] for i in symbols.get_sp500_symbols())

if not os.path.exists(basePath):
    os.makedirs(basePath)

with requests.Session() as s:
    download = s.get(request_url, params=request_params)
    with open(os.path.join(basePath, 'SPY.csv'), 'wb') as fd:
        fd.write(download.content)

    for stockTicker in SP500ticker:
        request_params['symbol'] = stockTicker
        download = s.get(request_url, params=request_params)
        with open(os.path.join(basePath, stockTicker + '.csv'), 'wb') as fd:
            fd.write(download.content)
