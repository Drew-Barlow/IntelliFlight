import json

"""
Map BTS airport IDs to FAA airport IDs, ICAO IDs, and
Meteostat weather station IDs.

If any of the above associations cannot be made (i.e.,
the relevant ID or weather station does not exist), the
airport is dropped from the data.
"""

mappings = []

# From https://transtats.bts.gov/Fields.asp?gnoyr_VQ=FGK (key OriginAirportID)
with open('L_AIRPORT.csv', 'r') as f_airport_faa_ids:
    # From https://en.wikipedia.org/wiki/List_of_airports_in_the_United_States
    # The table on that page was copied and converted to CSV.
    with open('wikitable.csv', 'r') as f_wiki_airports:
        # From https://github.com/meteostat/weather-stations (Lite dump)
        with open("meteostat_lite.json", 'r', encoding='utf-8') as f_meteostat_stations:
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
                            mappings.append({
                                # trim closing " and \n
                                'desc': ''.join(line.split(',')[1:])[1:-2],
                                'icao': icao,
                                'faa': line.split(',')[0][1:-1],
                                'mstat': station['id'],
                                'location': station['location']
                            })
                            station_found = True
                            success += 1

                    if not station_found:
                        # print(f'no weather station found for icao {icao}')
                        fail += 1

                else:
                    # print(f'no icao found for faa {line.split(",")[0][1:-1]}')
                    fail += 1

                print(f'success: {success} fail: {fail}')

# From https://transtats.bts.gov/Fields.asp?gnoyr_VQ=FGK (key Origin)
with open('L_AIRPORT_ID.csv') as f_bts_ids:
    idlines = f_bts_ids.readlines()
    for m in mappings:
        for l in idlines:
            if m['desc'] == ''.join(l.split(',')[1:])[1:-2]:
                m['bts_id'] = l.split(',')[0][1:-1]

print(f'generated {len(mappings)} records')

with open('../airport_mappings.json', 'w') as f_out:
    json.dump(mappings, f_out, indent=2)
