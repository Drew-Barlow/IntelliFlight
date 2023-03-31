import pytest
import json
from pathlib import Path
from schema import SchemaError
import intelliflight.util.datautil as datautil
from typing import Final
from datetime import datetime
from copy import deepcopy

TEST_PATH: Final = Path(__file__).parent.parent

VALID_MAP_PATH: Final = TEST_PATH / "data" / "valid_airport_mappings.json"
BAD_MAP_PATH: Final = TEST_PATH / 'data' / 'bad_airport_mappings.json'

VALID_WEATHER_PATH: Final = \
    TEST_PATH / 'data' / 'historical_weather_by_bts.json'

# Paths to sets of flight data for which only the first flight should
# merge with a weather data object
FLIGHTS_NO_TMP_OR_WND_PATH: Final = \
    TEST_PATH / 'data' / 'historical_flights_no_tmp_or_wnd.csv'
FLIGHTS_NO_WEATHER_FOR_DATE_PATH: Final = \
    TEST_PATH / 'data' / 'historical_flights_no_weather.csv'
FLIGHTS_NO_WEATHER_FOR_AIRPORT_PATH: Final = \
    TEST_PATH / 'data' / 'historical_flights_no_weather_for_airport.csv'
FLIGHTS_UNMAPPED_AIRPORTS_PATH: Final = \
    TEST_PATH / 'data' / 'historical_flights_unmapped_src_dst.csv'

# Output of merge on the above flight sets and weather
PARTIAL_MERGE_OUTPUT: Final = [{
    'DAY_OF_WEEK': '1',
    'FL_DATE': '1/1/2018 12:00:00 AM',
    'OP_UNIQUE_CARRIER': '9E',
    'ORIGIN_AIRPORT_ID': '10135',
    'DEST_AIRPORT_ID': '10135',
    'CRS_DEP_TIME': '1459',
    'DEP_DELAY_GROUP': '-1',
    'ARR_DELAY_GROUP': '-2',
    'CANCELLED': '0.00',
    'CANCELLATION_CODE': '',
    'DIVERTED': '0.00',
    'src_tavg': 10.0,
    'dst_tavg': 10.0,
    'src_wspd': 11.0,
    'dst_wspd': 11.0
}]


FLIGHTS_SEEN_CARRIERS_AND_AIRPORTS_PATH: Final = \
    TEST_PATH / 'data' / 'historical_flights_seen_carriers_airports.csv'

SEEN_CARRIERS_AIRPORTS_MERGE_OUTPUT: Final = [
    {
        'DAY_OF_WEEK': '1',
        'FL_DATE': '1/1/2018 12:00:00 AM',
        'OP_UNIQUE_CARRIER': '9E',
        'ORIGIN_AIRPORT_ID': '10135',
        'DEST_AIRPORT_ID': '10136',
        'CRS_DEP_TIME': '1459',
        'DEP_DELAY_GROUP': '-1',
        'ARR_DELAY_GROUP': '-2',
        'CANCELLED': '0.00',
        'CANCELLATION_CODE': '',
        'DIVERTED': '0.00',
        'src_tavg': 10.0,
        'dst_tavg': 5.0,
        'src_wspd': 11.0,
        'dst_wspd': 6.0
    },
    {
        'DAY_OF_WEEK': '1',
        'FL_DATE': '1/1/2018 12:00:00 AM',
        'OP_UNIQUE_CARRIER': '0F',
        'ORIGIN_AIRPORT_ID': '10135',
        'DEST_AIRPORT_ID': '10136',
        'CRS_DEP_TIME': '1459',
        'DEP_DELAY_GROUP': '-1',
        'ARR_DELAY_GROUP': '-2',
        'CANCELLED': '0.00',
        'CANCELLATION_CODE': '',
        'DIVERTED': '0.00',
        'src_tavg': 10.0,
        'dst_tavg': 5.0,
        'src_wspd': 11.0,
        'dst_wspd': 6.0
    }
]

FIFTY_FLIGHTS_PATH: Final = TEST_PATH / 'data' / 'fifty_flights.json'

DISCRETIZE_BASE_DATA: Final = [{
    "DAY_OF_WEEK": "1",
    "FL_DATE": "7/1/2019 12:00:00 AM",
    "OP_UNIQUE_CARRIER": "9E",
    "ORIGIN_AIRPORT_ID": "10135",
    "DEST_AIRPORT_ID": "10397",
    "CRS_DEP_TIME": "0000",
    "DEP_DELAY_GROUP": "-1",
    "ARR_DELAY_GROUP": "-2",
    "CANCELLED": "0.00",
    "CANCELLATION_CODE": "",
    "DIVERTED": "0.00",
    "src_tavg": 1.0,
    "dst_tavg": 1.0,
    "src_wspd": 1.0,
    "dst_wspd": 1.0
}]


@pytest.mark.unit
@pytest.mark.datautil
def test_merge_bad_flight_path():
    with pytest.raises(FileNotFoundError):
        datautil.merge_training_data('BAD_PATH', VALID_WEATHER_PATH)


@pytest.mark.unit
@pytest.mark.datautil
def test_merge_bad_weather_path():
    with pytest.raises(FileNotFoundError):
        datautil.merge_training_data(FLIGHTS_NO_TMP_OR_WND_PATH, 'BAD_PATH')


@pytest.mark.unit
@pytest.mark.datautil
@pytest.mark.parametrize('flight_data', [
    FLIGHTS_NO_TMP_OR_WND_PATH,
    FLIGHTS_NO_WEATHER_FOR_AIRPORT_PATH,
    FLIGHTS_NO_WEATHER_FOR_DATE_PATH,
    FLIGHTS_UNMAPPED_AIRPORTS_PATH
])
def test_merge_partial(flight_data: Path):
    merged, _, _, _ = datautil.merge_training_data(
        flight_data, VALID_WEATHER_PATH)
    assert merged == PARTIAL_MERGE_OUTPUT


@pytest.mark.unit
@pytest.mark.datautil
def test_merge_seen_carriers_airports():
    merged, carriers, src, dst = datautil.merge_training_data(
        FLIGHTS_SEEN_CARRIERS_AND_AIRPORTS_PATH, VALID_WEATHER_PATH)
    assert merged == SEEN_CARRIERS_AIRPORTS_MERGE_OUTPUT
    assert carriers == {'9E', '0F'}
    assert src == {'10135'}
    assert dst == {'10136'}


@pytest.mark.unit
@pytest.mark.datautil
def test_shuffle_and_partition():
    unshuffled_data = json.load(FIFTY_FLIGHTS_PATH.open())
    shuffled_data = unshuffled_data[:]
    partition_indices = datautil.shuffle_and_partition(shuffled_data, 1, 3)
    # Test that order is changed
    assert unshuffled_data != shuffled_data
    # Test that elements are the same
    assert all([row in unshuffled_data for row in shuffled_data])
    # Test that partition indices are correct
    assert partition_indices == [0, 16, 33]


@pytest.mark.unit
@pytest.mark.datautil
@pytest.mark.parametrize('temp, bucket', [
    (-15, 0),
    (-10, 1), (-5, 1),
    (0, 2),   (5, 2),
    (10, 3),  (15, 3),
    (20, 4),  (25, 4),
    (30, 5),  (35, 5),
    (40, 6),  (45, 6),
    (50, 7),  (55, 7),
    (60, 8),  (65, 8),
    (70, 9),  (75, 9),
    (80, 10), (85, 10),
    (90, 11), (95, 11),
    (100, 12)
])
def test_discretize_temp(temp, bucket):
    data = deepcopy(DISCRETIZE_BASE_DATA)
    data[0]['src_tavg'] = temp
    data[0]['dst_tavg'] = temp
    datautil.discretize(data)
    assert data[0]['src_tavg'] == str(bucket)
    assert data[0]['dst_tavg'] == str(bucket)


@ pytest.mark.unit
@ pytest.mark.datautil
@pytest.mark.parametrize('wind, bucket', [
    (0, 0),  (5, 0),
    (10, 1), (15, 1),
    (20, 2), (25, 2),
    (30, 3), (35, 3),
    (40, 4)
])
def test_discretize_wind(wind, bucket):
    data = deepcopy(DISCRETIZE_BASE_DATA)
    data[0]['src_wspd'] = wind
    data[0]['dst_wspd'] = wind
    datautil.discretize(data)
    assert data[0]['src_wspd'] == str(bucket)
    assert data[0]['dst_wspd'] == str(bucket)


@ pytest.mark.unit
@ pytest.mark.datautil
@pytest.mark.parametrize('time, bucket', [
    ('0000', '0000'),  ('0015', '0000'),
    ('0030', '0030'),  ('0045', '0030'),
])
def test_discretize_time(time, bucket):
    data = deepcopy(DISCRETIZE_BASE_DATA)
    data[0]['CRS_DEP_TIME'] = time
    datautil.discretize(data)
    assert data[0]['CRS_DEP_TIME'] == bucket
