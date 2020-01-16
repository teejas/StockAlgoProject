import os
import requests
import finsymbols as symbols
import time
import shutil
from config.config import Config

# get config values
config_data = Config().get()
basePath = config_data['paths']['raw_data_kibot']
api_url = config_data['kibot']['api_url']
username = config_data['kibot']['username']
password = config_data['kibot']['password']
request_params = config_data['kibot']['request_params']
exclude_symbols = config_data.get('kibot', 'exclude_symbols')

kibot_errors = {
    400: '400 Bad Request',
    401: '401 Not Logged In',
    402: '402 Unauthorized',
    403: '403 Login Failed',
    404: '404 Symbol Not Found',
    405: '405 Data Not Found',
    500: '500 Internal Server Error'
}

# get ticker symbols list
SP500ticker = list(i['symbol'] for i in symbols.get_sp500_symbols())
SP500ticker = [x for x in SP500ticker if x not in exclude_symbols]
SP500ticker = ['SPY'] + SP500ticker

# create output directory if needed
if os.path.exists(basePath):
    print 'cleaning old data...'  # may need to change this if we need to append
    shutil.rmtree(basePath)
if not os.path.exists(basePath):
    print 'creating output path ({})'.format(basePath)
    os.makedirs(basePath)


# login function with retry
def login(session, tries=10):
    if tries < 0:
        print 'Number of login tries exceeded.'
        return False

    response = session.get(api_url, params={'action':'login', 'user':username, 'password':password})
    if not response.status_code == 200 or response.text in [kibot_errors[403], kibot_errors[500]]:
        print 'login failed ({}). waiting 1 second and retrying.'.format(response.text)
        time.sleep(1)
        return login(session, tries - 1)

    # have to check response body because the fucks at kibot don't know how response codes work
    if response.text in [kibot_errors[400], kibot_errors[402]]:
        return False

    print 'login successful'
    print response.text
    return True


fatal_errors = [kibot_errors[400], kibot_errors[402], kibot_errors[404], kibot_errors[405], kibot_errors[500]]
def download(session, symbol):
    print 'fetching data for symbol \'{}\'...'.format(symbol)
    request_params['symbol'] = symbol

    response = session.get(api_url, params=request_params)
    if not response.status_code == 200 or response.text in fatal_errors:
        print 'failed to fetch data for symbol \'{}\' ({})'.format(symbol, response.text)
        return None

    if response.text == kibot_errors[401]:
        print '{}: attempting log in'.format(response.text)
        if login(session):
            return download(session. symbol)
        else:
            raise Error('LOGIN FAILURE')

    print 'download for symbol \'{}\' successful'.format(symbol)
    return response.content


with requests.Session() as session:
    login(session)

    count = 0
    for symbol in SP500ticker:
        count += 1

        download_data = download(session, symbol)
        if download_data:
            with open(os.path.join(basePath, symbol + '.csv'), 'wb') as fd:
                fd.write(download_data)
                print 'write successful to {}.csv ({}/{})'.format(symbol, count, len(SP500ticker))
