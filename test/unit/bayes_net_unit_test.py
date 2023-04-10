'''Unit tests for the Bayes_Net class.

This class is lightly tested for the following reasons:

- The vast majority of data processing occurs in component classes
  (e.g., FrequencyCounter), which have their own test cases.
- The Bayes_Net class performs extensive logging, and since its logic is
  primarily concerned with invoking functionality in component classes,
  this is often sufficient to ensure proper functioning.
'''


import csv
import pytest
import json
from pathlib import Path
from intelliflight.models.bayes_net import Bayes_Net, data_dir
from intelliflight.models.components.keymeta import KeyMeta
from intelliflight.models.components.dataset import Dataset
from intelliflight.models.components.frequencycounter import FrequencyCounter
from intelliflight.models.components.ptables import ProbabilityTables
from typing import Final
from datetime import datetime

from intelliflight.util import datautil

TEST_PATH: Final = Path(__file__).parent.parent
PARAMS_PATH: Final = TEST_PATH / 'data' / 'sample_bayes_params.json'
TRUNCATED_FLIGHT_DATA_PATH: Final = TEST_PATH / \
    'data' / 'FLIGHT_DATA_TRUNCATED.csv'


@pytest.mark.unit
@pytest.mark.bayes
def test_init_no_args():
    '''Test initialization of status keys and other components.'''
    bayes = Bayes_Net()
    assert set(bayes.key_meta.get_status_keys()) == {
        'cancel:A',
        'cancel:B',
        'cancel:C',
        'cancel:D',
        'divert',
        'delay:-2',
        'delay:-1',
        'delay:0',
        'delay:1',
        'delay:2',
        'delay:3',
        'delay:4',
        'delay:5',
        'delay:6',
        'delay:7',
        'delay:8',
        'delay:9',
        'delay:10',
        'delay:11',
        'delay:12',
    }
    assert not bayes.dataset.data_loaded()
    assert bayes.frequencies.get_status_counter() == None
    assert bayes.p_tables.get_p_status() == None


@pytest.mark.unit
@pytest.mark.bayes
def test_init_params():
    '''Test loading of model parameters from file.'''
    bayes = Bayes_Net(PARAMS_PATH.as_posix())

    with PARAMS_PATH.open() as params_f:
        in_data = json.load(params_f)

    assert bayes.rng_seed == in_data['training_rng_seed']
    assert bayes.key_meta.get_seen_airports() == set(in_data['seen_airports'])
    assert bayes.key_meta.get_seen_carriers() == set(in_data['seen_carriers'])
    assert bayes.p_tables.get_p_status(
    ) == in_data['p_tables']['arrival_status']
    assert bayes.p_tables.get_p_airline() == in_data['p_tables']['airline']
    assert bayes.p_tables.get_p_day() == in_data['p_tables']['day']
    assert bayes.p_tables.get_p_dep_time(
    ) == in_data['p_tables']['departure_time']
    assert bayes.p_tables.get_p_src() == in_data['p_tables']['src_airport']
    assert bayes.p_tables.get_p_dst() == in_data['p_tables']['dst_airport']
    assert bayes.p_tables.get_p_src_tmp(
    ) == in_data['p_tables']['src_temperature']
    assert bayes.p_tables.get_p_dst_tmp(
    ) == in_data['p_tables']['dst_temperature']
    assert bayes.p_tables.get_p_src_wnd(
    ) == in_data['p_tables']['src_wind_speed']
    assert bayes.p_tables.get_p_dst_wnd(
    ) == in_data['p_tables']['dst_wind_speed']


@pytest.mark.unit
@pytest.mark.bayes
def test_load_data():
    '''Test proper loading of data'''
    bayes = Bayes_Net()
    bayes.load_data(TRUNCATED_FLIGHT_DATA_PATH.as_posix())

    with TRUNCATED_FLIGHT_DATA_PATH.open() as flights_f:
        in_data = [row for row in csv.DictReader(flights_f)]

    # Filter weather data from loaded data (since we know datautil, which
    # merges flight and weather data, works)
    loaded_data_flights_only = [{
        key: row[key] for key in in_data[0].keys()
    } for row in bayes.dataset.get_data()]
    # Discretize raw data
    discretized_in_data = [{
        **row,
        "src_tavg": 0,
        "dst_tavg": 0,
        "src_wspd": 0,
        "dst_wspd": 0
    } for row in in_data]
    datautil.discretize(discretized_in_data)
    # Strip out weather fields (they were needed to discretize)
    discretized_in_data = [{
        key: row[key] for key in in_data[0].keys()
    } for row in discretized_in_data]

    # Note that some flights from in_data may be pruned from the loaded data
    # for various reasons
    assert all([
        row in discretized_in_data for row in loaded_data_flights_only
    ])
    assert bayes.key_meta.get_seen_airports().issubset(set([
        *[row['ORIGIN_AIRPORT_ID'] for row in in_data],
        *[row['DEST_AIRPORT_ID'] for row in in_data]
    ]))
    assert bayes.key_meta.get_seen_carriers().issubset(set([
        row['OP_UNIQUE_CARRIER'] for row in in_data
    ]))


@pytest.mark.unit
@pytest.mark.bayes
def test_export_parameters():
    '''Test exporting of model parameters.'''
    model_path = (data_dir / 'models' / 'bayes_net.model.json')
    # Backup existing model file
    backup_time = None
    if model_path.exists():
        backup_time = datetime.now().isoformat().replace(':', '.')
        model_path.rename(
            (data_dir / 'models' / f'bayes_net.model.json.{backup_time}.bak'))

    # Export
    bayes = Bayes_Net(PARAMS_PATH.as_posix())
    bayes.export_parameters()

    # Test result
    with PARAMS_PATH.open() as params_f:
        in_data = json.load(params_f)

    # Do not immediately assert since we need to do cleanup
    test_data = json.load(model_path.open())

    in_data['seen_airports'] = set(in_data['seen_airports'])
    test_data['seen_airports'] = set(test_data['seen_airports'])
    in_data['seen_carriers'] = set(in_data['seen_carriers'])
    test_data['seen_carriers'] = set(test_data['seen_carriers'])

    # Delete test model file
    model_path.unlink()

    # Restore old model
    if backup_time is not None:
        (data_dir / 'models' /
         f'bayes_net.model.json.{backup_time}.bak').rename(model_path)

    assert in_data == test_data
