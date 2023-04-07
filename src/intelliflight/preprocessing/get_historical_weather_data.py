from pathlib import Path
import requests
from typing import Final
import json
import sys
import datetime
import time

"""
Usage: python ./get_historical_weather_data.py <METEOSTAT_API_KEY>

airport_mappings.json is assumed to be in the same folder.

Output format is:
{
    <Airport BTS ID>: {
        <YYYY-MM-DD>: {
            'date': <YYYY-MM-DD>
            <weather fields>
        }
    },
    ...
}
For information about weather fields, see:
https://dev.meteostat.net/api/stations/daily.html#data-response

All units are imperial.

USING THE OUTPUT DATA IN PYTHON:
To access the data for a particular day and airport, run the following:

import json
data = {}
with open('PATH/TO/historical_weather_by_bts_id.json', 'r') as f:
    data = json.load(f)

# Access weather on a certain day at a certain airport
data['<Airport BTS ID>']['<Day in YYYY-MM-DD format>']

"""

data_dir = Path(__file__).parent.parent.parent.parent / 'data'

start_time = datetime.datetime.now()
mappings = []

with (data_dir / 'maps' / 'airport_mappings.json').open('r') as map_f:
    mappings = json.load(map_f)

if len(sys.argv) < 2:
    print('Error: Meteostat API key required as an argument')
    exit(0)

METEOSTAT_KEY: Final = sys.argv[1]

failed_mappings = []
historical_data = {}
i = 1
for m in mappings:
    # Print status
    # \033[K - ANSI code to erase to end of line
    # \r - carriage return - move cursor to beginning of current line
    print(
        f'\033[K{i}/{len(mappings)}: Fetching weather for {m["desc"]} (Meteostat ID {m["mstat"]})\r', end='')

    # Make API request
    res: requests.Response = requests.get('https://meteostat.p.rapidapi.com/stations/daily', headers={
        'x-rapidapi-host': 'meteostat.p.rapidapi.com',
        'x-rapidapi-key': METEOSTAT_KEY
    }, params={
        'model': 'false',
        'units': 'imperial',
        'start': '2018-01-01',
        'end': '2022-12-31',
        'station': m['mstat']
    })

    # Check for error
    if res.status_code != 200:
        failed_mappings.append({
            'code': res.status_code,
            'msg': res.text,
            'mapping': m
        })

    else:
        # Format {'meta': {...}, 'data': [...]}
        data_j = res.json()
        # Format [{'data': <YYYY-MM-DD>, <weather data>}, ...]
        data_l = data_j['data']
        historical_data[m['bts_id']] = {}
        for day in data_l:
            historical_data[m['bts_id']][day['date']] = day

    # Sleep to avoid rate limit
    time.sleep(0.5)
    i += 1

# Output results
print('\nWriting output file...')
with (data_dir / 'historical' / 'weather' / 'weather_by_bts_id.json').open('w') as out_f:
    out_f.write(json.dumps(historical_data, indent=2))

if len(failed_mappings) > 0:
    with (data_dir / 'historical' / 'weather' / 'failed_weather_requests.json').open('w') as out_f:
        out_f.write(json.dumps(failed_mappings, indent=2))

print(
    f'Completed in {datetime.datetime.now().timestamp() - start_time.timestamp()}s')
