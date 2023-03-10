import sys
import json
import requests
import datetime
import time
import os.path as path
from typing import Final

from ..intelliflight.util.nws_manager import Forecaster

AIRPORT_MAP_PATH: Final = '../data/maps/airport_mappings.json'

start_time = datetime.datetime.now()
mappings = []
with open(AIRPORT_MAP_PATH, 'r') as mappings_f:
    print('Loaded map file')
    mappings = json.load(mappings_f)

success = 0
fail = 0
server_err = 0
total = 0

failed_bts = []

f = Forecaster(AIRPORT_MAP_PATH)
t = datetime.datetime.now().isoformat()

i = 0
backoff = 0
delay = 5
while i < len(mappings):
    m = mappings[i]
    try:
        print(
            f'\033[K{i + 1}/{len(mappings)}: Testing {m["desc"]} ({m["bts_id"]})\r', end='')
        f.get_nws_forecast_from_bts(int(m['bts_id']), t)
        success += 1
        backoff = 0
        i += 1

    except Exception as e:
        if e.__class__ == ConnectionError and json.loads(f'{{{str(e).split("{", 1)[1]}')['status'] == 500:
            server_err += 1
            print(f'\nError 500. Retrying in {backoff + delay}s...')
            if backoff > 0:
                time.sleep(backoff)
            backoff += delay

        else:
            print(f'\nError on BTS {m["bts_id"]}: {e}')
            i += 1
            fail += 1
            failed_bts.append(m['bts_id'])
            backoff = 0

    finally:
        total += 1
        time.sleep(delay)
if len(failed_bts) > 0:
    print('Failure on the following BTS IDs:')
    for bts in failed_bts:
        print(bts)
print(f'\n{success} successes\t{fail} failures')
print(f'{server_err} error 500s out of {total} requests')
print(
    f'Completed in {datetime.datetime.now().timestamp() - start_time.timestamp()}s')
