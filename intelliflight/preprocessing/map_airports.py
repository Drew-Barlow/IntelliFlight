import json
from ..preprocessing import DATA_PATH

"""
Map BTS airport IDs to FAA airport IDs, ICAO IDs, and
Meteostat weather station IDs.

If any of the above associations cannot be made (i.e.,
the relevant ID or weather station does not exist), the
airport is dropped from the data.
"""

mappings = []

icao_coords = []
# From https://ourairports.com/data/
with open(f'{DATA_PATH}/raw/airports/airports.csv', 'r', encoding='utf-8') as f_airport_db:
    for l in f_airport_db.readlines():
        tokens = l.split(',')
        # Check country code. Remove surrounding quotes.
        if tokens[8][1:-1] in ['US', 'PR', 'UM', 'AS', 'GU', 'MP', 'VI']:
            icao_coords.append({
                # Remove surrounding quotes from ICAO
                'icao': tokens[1][1:-1],
                'lat': tokens[4],
                'lon': tokens[5]
            })

# From https://transtats.bts.gov/Fields.asp?gnoyr_VQ=FGK (key OriginAirportID)
with open(f'{DATA_PATH}/raw/airports/L_AIRPORT.csv', 'r') as f_airport_faa_ids:
    # From https://en.wikipedia.org/wiki/List_of_airports_in_the_United_States
    # The table on that page was copied and converted to CSV.
    with open(f'{DATA_PATH}/raw/airports/wikitable.csv', 'r') as f_wiki_airports:
        # From https://github.com/meteostat/weather-stations (Lite dump)
        with open(f'{DATA_PATH}/raw/weather/meteostat_lite.json', 'r', encoding='utf-8') as f_meteostat_stations:
            wikilines = f_wiki_airports.readlines()
            meteostat = json.load(f_meteostat_stations)
            success = 0
            fail = 0
            for line in f_airport_faa_ids.readlines()[1:]:
                icao = None
                for wikiline in wikilines:
                    tokens = wikiline.split(',')
                    if tokens[1] == line.split(',')[0][1:-1]:
                        icao = tokens[3]

                if icao is not None:
                    station_found = False
                    for station in meteostat:
                        if station['identifiers']['icao'] == icao:
                            location = {}
                            for coord_obj in icao_coords:
                                if coord_obj['icao'] == icao:
                                    location['lat'] = coord_obj['lat']
                                    location['lon'] = coord_obj['lon']
                                    break

                            if location == {}:
                                fail += 1
                                station_found = True
                                # print(f'fail _{icao}_')

                            else:
                                mappings.append({
                                    # trim closing " and \n
                                    'desc': ''.join(line.split(',')[1:])[1:-2],
                                    'icao': icao,
                                    'faa': line.split(',')[0][1:-1],
                                    'mstat': station['id'],
                                    'location': location
                                })
                                station_found = True
                                success += 1

                    if not station_found:
                        # print(f'no weather station found for icao {icao}')
                        fail += 1

                else:
                    # print(f'no icao found for faa {line.split(",")[0][1:-1]}')
                    fail += 1

                # print(f'success: {success} fail: {fail}')

# From https://transtats.bts.gov/Fields.asp?gnoyr_VQ=FGK (key Origin)
final_mappings = []
with open(f'{DATA_PATH}/raw/airports/L_AIRPORT_ID.csv') as f_bts_ids:
    idlines = f_bts_ids.readlines()
    s = 0
    f = 0
    for m in mappings:
        found = False
        for l in idlines:
            if m['desc'] == ''.join(l.split(',')[1:])[1:-2]:
                m['bts_id'] = l.split(',')[0][1:-1]
                s += 1
                found = True
                final_mappings.append(m)

        if not found:
            f += 1

    # print(f's {s} f {f}')

print(f'generated {len(final_mappings)} records')

with open(f'{DATA_PATH}/maps/airport_mappings.json', 'w') as f_out:
    json.dump(final_mappings, f_out, indent=2)
