import sys
import requests
from urllib3 import disable_warnings
import json
from time import sleep
import platform
import psutil
import base64

# suppress warnings
# requests.packages.urllib3.disable_warnings()
disable_warnings()

# global variables
app_port = None
auth_token = None
region = None
lcu_name = None  # LeagueClientUx executable name

# functions
def getLCUName():
    '''
    Get LeagueClient executable name depending on platform.
    '''
    global lcu_name
    if platform.system() == 'Windows':
        lcu_name = 'LeagueClientUx.exe'
    elif platform.system() == 'Darwin':
        lcu_name = 'LeagueClientUx'
    elif platform.system() == 'Linux':
        lcu_name = 'LeagueClientUx'


def LCUAvailable():
    '''
    Check whether a client is available.
    '''
    return lcu_name in (p.name() for p in psutil.process_iter())


def getLCUArguments():
    global auth_token, app_port, region
    '''
    Get region, remoting-auth-token and app-port for LeagueClientUx.
    '''
    if not LCUAvailable():
        sys.exit('No ' + lcu_name + ' found. Login to an account and try again.')

    for p in psutil.process_iter():
        if p.name() == lcu_name:
            args = p.cmdline()

            for a in args:
                if '--region=' in a:
                    region = a.split('--region=', 1)[1].lower()
                if '--remoting-auth-token=' in a:
                    auth_token = a.split('--remoting-auth-token=', 1)[1]
                if '--app-port' in a:
                    app_port = a.split('--app-port=', 1)[1]


def main():
    # get LeagueClient name
    getLCUName()

    # get app port & auth token for each client
    getLCUArguments()

    api = 'https://127.0.0.1:' + app_port

    session_token = base64.b64encode(
        ('riot:' + auth_token).encode('ascii')).decode('ascii')

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + session_token
    }

    # get current summoner
    get_current_summoner = api + '/lol-summoner/v1/current-summoner'

    r = requests.get(get_current_summoner, headers=headers, verify=False)
    r = json.loads(r.text)

    print('Connected: ' + r['displayName'])

    # get champ select
    while True:
        get_champ_select = api + '/lol-champ-select/v1/session'

        r = requests.get(get_champ_select, headers=headers, verify=False)
        r = json.loads(r.text)

        # if 'httpStatus' in r and r['httpStatus'] == 404:
        if 'errorCode' in r:
            print('Not in champ select.')
            sleep(2)
        else:
            print('\n* Found lobby. *\n')
            # format_response = json.dumps(r, indent=2)
            # print(format_response)

            for x in r['myTeam']:
                get_summoner_by_id = api + '/lol-summoner/v1/summoners/' + str(x['summonerId'])

                r = requests.get(get_summoner_by_id, headers=headers, verify=False)
                r = json.loads(r.text)

                print(r['displayName'] + ' joined the lobby')

            break

    # keep main thread alive
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == '__main__':
    main()
