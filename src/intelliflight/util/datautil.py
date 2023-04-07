import json
import csv
from pathlib import Path
import random
import math

from bisect import bisect_right
from intelliflight.util import typeutil

from intelliflight.constants import WEATHER_FIELDS, TIME_INTERVAL_SIZE


data_dir = Path(__file__).parent.parent.parent.parent / 'data'


def merge_training_data(flight_path: str, weather_path: str):
    """Merge data & collate data keys contained therein.

    Positional vrguments:

    - flight_path -- path to flight data file
    - weather_path -- path to weather data file

    Returns:

    - merged_data -- list whose rows contain combined flight and weather data
                     whose properties are described in the Post-conditions
                     section below
    - seen_carriers -- set of airline codes present in `merged_data`
    - seen_src -- set of airport bts_id values seen as flight sources in
                  `merged_data`
    - seen_dst -- set of airport bts_id values seen as flight destinations
                  in `merged_data`

    Post-conditions:

    - Flights for which no weather data exist are pruned.
    - Flights to or from unknown airports (those not in airport_mappings.json)
      are pruned.
    - Records contain the following keys:
      - all keys in original flight data
      - `src_tavg` (temperature at source)
      - `dst_tavg` (temperature at destination)
      - `src_wspd` (wind speed at source)
      - `dst_wspd` (wind speed at destination)
    - Data are NOT discretized at this stage.
    """
    flight_data = []
    weather_data = None
    known_airports = None
    # Read data from files
    with open(flight_path, 'r', encoding="utf-8") as f_in, \
            open(weather_path, 'r', encoding="utf-8") as w_in, \
        (data_dir / 'maps' / 'airport_mappings.json').open(encoding="utf-8") as a_in:
        # Load known airport mappings
        mappings = json.load(a_in)
        typeutil.AIRPORT_MAP_SCHEMA.validate(mappings)
        known_airports = [i['bts_id'] for i in mappings]

        # Load weather data
        weather_data = json.load(w_in)

        # Load flight data
        for row in csv.DictReader(f_in):
            flight_data.append(row)

    merged_data = []
    seen_carriers = set()
    seen_src = set()
    seen_dst = set()

    for row in flight_data:
        # date_arr = Flight date in [month, day, year] format
        date_arr = row['FL_DATE'].split(' ')[0].split('/')
        # Convert to YYYY-MM-DD string
        ymd_date = f'{date_arr[2]}-{date_arr[0].rjust(2, "0")}-{date_arr[1].rjust(2, "0")}'

        # Check that weather data exists for the source and destination airports
        # Also check that src and dst airports are known
        # First, check that src and dst airports are in weather data
        # Next, check that the relevant date has weather data for src and dst
        # Finally, check that src and dst are known in the mappings file
        if str(row['ORIGIN_AIRPORT_ID']) in weather_data.keys() and str(row['DEST_AIRPORT_ID']) in weather_data.keys() \
                and ymd_date in weather_data[str(row['ORIGIN_AIRPORT_ID'])].keys() \
                and ymd_date in weather_data[str(row['DEST_AIRPORT_ID'])].keys() \
                and str(row['ORIGIN_AIRPORT_ID']) in known_airports and str(row['DEST_AIRPORT_ID']) in known_airports:
            # Read flight data at source and destination
            flight_weather = {
                'src': weather_data[str(row['ORIGIN_AIRPORT_ID'])][ymd_date],
                'dst': weather_data[str(row['DEST_AIRPORT_ID'])][ymd_date]
            }
            # Check that for source and destination weather,
            # all relevant weather fields exist (i.e., are not null).
            if all([all([i[key['historical']] is not None for i in flight_weather.values()]) for key in WEATHER_FIELDS]):
                # Generate merged data point
                merged_row = row
                for key in [i['historical'] for i in WEATHER_FIELDS]:
                    merged_row[f'src_{key}'] = flight_weather['src'][key]
                    merged_row[f'dst_{key}'] = flight_weather['dst'][key]

                merged_data.append(merged_row)
                seen_src.add(str(row['ORIGIN_AIRPORT_ID']))
                seen_dst.add(str(row['DEST_AIRPORT_ID']))
                seen_carriers.add(str(row['OP_UNIQUE_CARRIER']))

    return merged_data, seen_carriers, seen_src, seen_dst


def shuffle_and_partition(dataset: list, rng_seed: int, partition_count: int) -> list[int]:
    """Shuffle dataset in-place with passed RNG seed and return partition starting indices.

    Positional arguments:

    - dataset -- list of data to be shuffled in-place with `random.shuffle()`
    - rng_seed -- seed value for `random.seed()`
    - partition_count -- number of data partitions to generate

    Returns:

    List of starting indices for each partition in dataset

    Post-conditions:

    - RNG is reseeded based on `rng_seed`
    - `dataset` is shuffled
    """
    # Shuffle dataset in-place
    random.seed(rng_seed)
    random.shuffle(dataset)
    # Get exact starting position of each partition
    l = len(dataset)
    partition_size = l / partition_count
    partition_indices = [0]
    for i in range(partition_count - 1):
        partition_indices.append(partition_indices[i] + partition_size)

    # Floor partition indices to integer values
    return [math.floor(i) for i in partition_indices]


def discretize(dataset: list):
    """Discretize weather and time data in-place.

    Positional Arguments:

    A list of data dicts containing at least the following keys:
    - `src_tavg` (float)   -- temperature at source
    - `dst_tavg` (float)   -- temperature at destination
    - `src_wspd` (float)   -- wind speed at source
    - `dst_wspd` (float)   -- wind speed at destination
    - `CRS_DEP_TIME` (str) -- military time (24h clock) in `hhmm` format

    Post-conditions:

    - Weather fields are discretized to codes in the relevant `data/map` file.
    - Departure time is floored to a 30-minute increment (`hh00` or `hh30`).
    - All data keys other than those specified above are untouched.
    """
    wind_map = None
    temp_map = None
    with (data_dir / 'maps' / 'wind_speeds.csv').open('r', encoding='utf-8') as w_in, \
            (data_dir / 'maps' / 'temp_ranges.csv').open('r', encoding='utf-8') as t_in:
        wind_map = list(csv.DictReader(w_in))
        temp_map = list(csv.DictReader(t_in))

    for row in dataset:
        for prefix in ['src_', 'dst_']:
            # Discretize temperature
            temp = row[f'{prefix}tavg']
            thresholds = [float(i['min']) for i in temp_map[1:]]
            index = bisect_right(thresholds, temp)
            row[f'{prefix}tavg'] = temp_map[index]['key']

            # Discretize wind speed
            wind = row[f'{prefix}wspd']
            thresholds = [float(i['min']) for i in wind_map[1:]]
            index = bisect_right(thresholds, wind)
            row[f'{prefix}wspd'] = temp_map[index]['key']

        # Discretize timestamp into 30min segments
        dep_time = row['CRS_DEP_TIME']
        # Convert minute portion of timestamp to int, floor to
        # TIME_INTERVAL_SIZE increment, and update timestamp
        dep_min = int(dep_time[2:])
        new_min = str(dep_min - (dep_min % TIME_INTERVAL_SIZE))
        row['CRS_DEP_TIME'] = f'{dep_time[:2]}{new_min.rjust(2, "0")}'
