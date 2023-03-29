import json
import csv
import random
import math

from bisect import bisect_right

from ..constants import WEATHER_FIELDS, TIME_INTERVAL_SIZE
from ..util import DATA_PATH


def merge_training_data(flight_path: str, weather_path: str):
    """Merge data & compile keys"""
    flight_data = []
    weather_data = None
    known_airports = None
    # Read data from files
    with open(flight_path, 'r', encoding="utf-8") as f_in, \
            open(weather_path, 'r', encoding="utf-8") as w_in, \
            open(f'data/maps/airport_mappings.json', encoding="utf-8") as a_in:
        known_airports = [i['bts_id'] for i in json.load(a_in)]
        weather_data = json.load(w_in)
        for row in csv.DictReader(f_in):
            flight_data.append(row)

    merged_data = []
    seen_carriers = set()
    seen_src = set()
    seen_dst = set()

    for row in flight_data:
        # Flight date, [month, day, year]
        date_arr = row['FL_DATE'].split(' ')[0].split('/')
        # Convert to YYYY-MM-DD
        ymd_date = f'{date_arr[2]}-{date_arr[0].rjust(2, "0")}-{date_arr[1].rjust(2, "0")}'
        # Check that weather data exists for the source and destination airports
        # Also check that src and dst airports are known
        if str(row['ORIGIN_AIRPORT_ID']) in weather_data.keys() and str(row['DEST_AIRPORT_ID']) in weather_data.keys() and \
                str(row['ORIGIN_AIRPORT_ID']) in known_airports and str(row['DEST_AIRPORT_ID']) in known_airports:
            flight_weather = {
                'src': weather_data[str(row['ORIGIN_AIRPORT_ID'])][ymd_date],
                'dst': weather_data[str(row['DEST_AIRPORT_ID'])][ymd_date]
            }
            # Check that for source and destination weather, all relevant weather fields exist.
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
    dataset -- list of data to be shuffled in-place with random.shuffle()
    rng_seed -- seed value for random.seed()
    partition_count -- number of data partitions to generate

    Returns:
    List of starting indices for each partition in dataset
    """
    # Shuffle dataset in-place
    random.seed(rng_seed)
    random.shuffle(dataset)
    # Get starting index of each partition
    l = len(dataset)
    partition_size = l / partition_count
    partition_indices = [0]
    for i in range(partition_count - 1):
        partition_indices.append(partition_indices[i] + partition_size)

    # Floor partition indices to integer values
    return [math.floor(i) for i in partition_indices]


def discretize(dataset: list):
    """Discretize dataset in-place."""
    wind_map = None
    temp_map = None
    with open('data/maps/wind_speeds.csv', 'r', encoding='utf-8') as w_in, \
            open('data/maps/temp_ranges.csv', 'r', encoding='utf-8') as t_in:
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
        dep_min = int(dep_time[2:])
        row['CRS_DEP_TIME'] = f'{dep_time[:2]}{str(dep_min - (dep_min % TIME_INTERVAL_SIZE)).rjust(2, "0")}'
