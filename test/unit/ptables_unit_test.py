import pytest
import json
from pathlib import Path
from intelliflight.models.components.keymeta import KeyMeta
from intelliflight.models.components.dataset import Dataset
from intelliflight.models.components.frequencycounter import FrequencyCounter
from intelliflight.models.components.ptables import ProbabilityTables
from typing import Final


## DATA ##


TEST_PATH: Final = Path(__file__).parent.parent
FREQ_TEST_DATA_PATH: Final = TEST_PATH / 'data' / 'freq_test_data.json'
DEP_TIME_KEYS: Final = frozenset([
    '0000', '0030',
    '0100', '0130',
    '0200', '0230',
    '0300', '0330',
    '0400', '0430',
    '0500', '0530',
    '0600', '0630',
    '0700', '0730',
    '0800', '0830',
    '0900', '0930',
    '1000', '1030',
    '1100', '1130',
    '1200', '1230',
    '1300', '1330',
    '1400', '1430',
    '1500', '1530',
    '1600', '1630',
    '1700', '1730',
    '1800', '1830',
    '1900', '1930',
    '2000', '2030',
    '2100', '2130',
    '2200', '2230',
    '2300', '2330',
])


## HELPERS ##


def get_dataset() -> Dataset:
    """Instantiate and return a Dataset object."""
    data = json.load(FREQ_TEST_DATA_PATH.open())
    dataset = Dataset()
    dataset.set_data(data)
    return dataset


def get_keymeta() -> KeyMeta:
    """Instantiate and return a KeyMeta object."""
    keymeta = KeyMeta()
    keymeta.set_arrival_statuses({
        'divert': 'desc1',
        'cancel:1': 'desc2',
        'delay:1': 'desc3',
        'delay:2': 'desc4'
    })
    keymeta.set_seen_airports({'a1', 'a2'})
    keymeta.set_seen_carriers({'c1', 'c2'})
    keymeta.set_temp_keys([1, 2])
    keymeta.set_wind_keys([1, 2])
    return keymeta


def get_zeroed_counter():
    counter = FrequencyCounter()
    counter.reset_counters(get_keymeta())
    return counter


def setup_counter():
    counter = FrequencyCounter()
    counter.reset_counters(get_keymeta())
    counter.count_frequencies(get_dataset())
    return counter


def setup_ptables(k: int):
    tables = ProbabilityTables()
    keymeta = get_keymeta()
    dataset = get_dataset()
    counter = FrequencyCounter()
    counter.reset_counters(keymeta)
    counter.count_frequencies(dataset)
    tables.reset_tables(keymeta, counter)
    tables.fit(dataset, counter, k)
    return tables

## TESTS ##


@pytest.mark.unit
@pytest.mark.ptables
def test_reset_tables():
    """Test initialization of table keys and values.
    Also tests `get_p_<x>()` and `query_p_<x>()`, which
    are used in the process of retrieving initialized values.
    """
    tables = ProbabilityTables()
    tables.reset_tables(get_keymeta(), get_zeroed_counter())

    # Check status table
    status_keys = {'divert', 'cancel:1', 'delay:1', 'delay:2'}
    assert set(tables.get_p_status().keys()) == status_keys
    for key in status_keys:
        assert tables.query_p_status(key) == 0

    # Check day table
    day_keys = {'1', '2', '3', '4', '5', '6', '7'}
    day_table = tables.get_p_day()
    assert set(day_table.keys()) == day_keys
    for key in day_keys:
        assert set(day_table[key].keys()) == status_keys
        for status_k in status_keys:
            assert tables.query_p_day(key, status_k) == 0

    # Check airline table
    airline_keys = {'c1', 'c2'}
    airline_table = tables.get_p_airline()
    assert set(airline_table.keys()) == airline_keys
    for key in airline_keys:
        assert set(airline_table[key].keys()) == status_keys
        for status_k in status_keys:
            assert tables.query_p_airline(key, status_k) == 0

    # Check src table
    src_keys = {'a1', 'a2'}
    src_table = tables.get_p_src()
    assert set(src_table.keys()) == src_keys
    for key in src_keys:
        assert set(src_table[key].keys()) == status_keys
        for status_k in status_keys:
            assert tables.query_p_src(key, status_k) == 0

    # Check dst table
    dst_keys = src_keys
    dst_table = tables.get_p_dst()
    assert set(dst_table.keys()) == dst_keys
    for key in dst_keys:
        assert set(dst_table[key].keys()) == status_keys
        for status_k in status_keys:
            assert tables.query_p_dst(key, status_k) == 0

    # Check dep_time table
    dep_time_table = tables.get_p_dep_time()
    assert frozenset(dep_time_table.keys()) == DEP_TIME_KEYS
    for key in DEP_TIME_KEYS:
        assert set(dep_time_table[key].keys()) == status_keys
        for status_k in status_keys:
            assert tables.query_p_dep_time(key, status_k) == 0

    # Check src_tmp table
    src_tmp_keys = {1, 2}
    src_tmp_table = tables.get_p_src_tmp()
    assert set(src_tmp_table.keys()) == src_tmp_keys
    for key in src_tmp_keys:
        assert set(src_tmp_table[key].keys()) == status_keys
        for status_k in status_keys:
            assert tables.query_p_src_tmp(key, status_k) == 0

    # Check dst_tmp table
    dst_tmp_keys = src_tmp_keys
    dst_tmp_table = tables.get_p_dst_tmp()
    assert set(dst_tmp_table.keys()) == dst_tmp_keys
    for key in dst_tmp_keys:
        assert set(dst_tmp_table[key].keys()) == status_keys
        for status_k in status_keys:
            assert tables.query_p_dst_tmp(key, status_k) == 0

    # Check src_wind table
    src_wind_keys = {1, 2}
    src_wind_table = tables.get_p_src_wnd()
    assert set(src_wind_table.keys()) == src_wind_keys
    for key in src_wind_keys:
        assert set(src_wind_table[key].keys()) == status_keys
        for status_k in status_keys:
            assert tables.query_p_src_wnd(key, status_k) == 0

    # Check dst_wind table
    dst_wind_keys = src_wind_keys
    dst_wind_table = tables.get_p_dst_wnd()
    assert set(dst_wind_table.keys()) == dst_wind_keys
    for key in dst_wind_keys:
        assert set(dst_wind_table[key].keys()) == status_keys
        for status_k in status_keys:
            assert tables.query_p_dst_wnd(key, status_k) == 0


@pytest.mark.unit
@pytest.mark.ptables
def test_fit_uninitialized():
    """Try to fit a `ProbabilityTables` whose values are uninitialized."""
    tables = ProbabilityTables()
    with pytest.raises(BufferError):
        tables.fit(get_dataset(), setup_counter(), 1)


# In the following tests, the calculated p tables are compared to hard-coded
# known correct values. Frequency data comes from the same source as the
# FrequencyCounter unit tests, and the expected outputs there show what
# frequency values were used to generate these probabilities.
# Frozen sets are used to make item order irrelevant while preserving
# hashability (which is necessary for assert)


@pytest.mark.unit
@pytest.mark.ptables
@pytest.mark.parametrize('k, expected', [
    (0, {
        ('divert', 0.2),
        ('cancel:1', 0.4),
        ('delay:1', 0.2),
        ('delay:2', 0.2)
    }),
    (1, {
        ('divert', 2 / 9),
        ('cancel:1', 3 / 9),
        ('delay:1', 2 / 9),
        ('delay:2', 2 / 9)
    })
])
def test_fit_statuses(k: int, expected: set[tuple[str, float]]):
    """Test fitting arrival status probabilities.

    k -- smoothing factor
    """
    tables = setup_ptables(k)

    # Check status counter
    status_table = tables.get_p_status()
    assert set(status_table.items()) == expected


@pytest.mark.unit
@pytest.mark.ptables
@pytest.mark.parametrize('k, expected', [
    (0, frozenset([
        ('1', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 1),
            ('delay:2', 0)
        ])),
        ('2', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 1)
        ])),
        ('3', frozenset([
            ('divert', 1),
            ('cancel:1', 0.5),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('4', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('5', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('6', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('7', frozenset([
            ('divert', 0),
            ('cancel:1', 0.5),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
    ])),
    (1, frozenset([
        ('1', frozenset([
            ('divert', 1 / 8),
            ('cancel:1', 1 / 9),
            ('delay:1', 2 / 8),
            ('delay:2', 1 / 8)
        ])),
        ('2', frozenset([
            ('divert', 1 / 8),
            ('cancel:1', 1 / 9),
            ('delay:1', 1 / 8),
            ('delay:2', 2 / 8)
        ])),
        ('3', frozenset([
            ('divert', 2 / 8),
            ('cancel:1', 2 / 9),
            ('delay:1', 1 / 8),
            ('delay:2', 1 / 8)
        ])),
        ('4', frozenset([
            ('divert', 1 / 8),
            ('cancel:1', 1 / 9),
            ('delay:1', 1 / 8),
            ('delay:2', 1 / 8)
        ])),
        ('5', frozenset([
            ('divert', 1 / 8),
            ('cancel:1', 1 / 9),
            ('delay:1', 1 / 8),
            ('delay:2', 1 / 8)
        ])),
        ('6', frozenset([
            ('divert', 1 / 8),
            ('cancel:1', 1 / 9),
            ('delay:1', 1 / 8),
            ('delay:2', 1 / 8)
        ])),
        ('7', frozenset([
            ('divert', 1 / 8),
            ('cancel:1', 2 / 9),
            ('delay:1', 1 / 8),
            ('delay:2', 1 / 8)
        ])),
    ]))
])
def test_fit_days(k: int, expected: set[tuple[str, float]]):
    """Test fitting day probabilities.

    k -- smoothing factor
    """
    tables = setup_ptables(k)

    # Check status counter
    table = tables.get_p_day()
    assert frozenset([(key, frozenset(col.items()))
                     for key, col in table.items()]) == expected


@pytest.mark.unit
@pytest.mark.ptables
@pytest.mark.parametrize('k, expected', [
    (0, frozenset([
        ('c1', frozenset([
            ('divert', 1),
            ('cancel:1', 0.5),
            ('delay:1', 1),
            ('delay:2', 1)
        ])),
        ('c2', frozenset([
            ('divert', 0),
            ('cancel:1', 0.5),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
    ])),
    (1, frozenset([
        ('c1', frozenset([
            ('divert', 2 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 2 / 3),
            ('delay:2', 2 / 3)
        ])),
        ('c2', frozenset([
            ('divert', 1 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 1 / 3),
            ('delay:2', 1 / 3)
        ])),
    ]))
])
def test_fit_airlines(k: int, expected: set[tuple[str, float]]):
    """Test fitting airline probabilities.

    k -- smoothing factor
    """
    tables = setup_ptables(k)

    # Check status counter
    table = tables.get_p_airline()
    assert frozenset([(key, frozenset(col.items()))
                     for key, col in table.items()]) == expected


@pytest.mark.unit
@pytest.mark.ptables
@pytest.mark.parametrize('k, expected', [
    (0, frozenset([
        ('a1', frozenset([
            ('divert', 1),
            ('cancel:1', 0.5),
            ('delay:1', 1),
            ('delay:2', 0)
        ])),
        ('a2', frozenset([
            ('divert', 0),
            ('cancel:1', 0.5),
            ('delay:1', 0),
            ('delay:2', 1)
        ])),
    ])),
    (1, frozenset([
        ('a1', frozenset([
            ('divert', 2 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 2 / 3),
            ('delay:2', 1 / 3)
        ])),
        ('a2', frozenset([
            ('divert', 1 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 1 / 3),
            ('delay:2', 2 / 3)
        ])),
    ]))
])
def test_fit_src(k: int, expected: set[tuple[str, float]]):
    """Test fitting source airport probabilities.

    k -- smoothing factor
    """
    tables = setup_ptables(k)

    # Check status counter
    table = tables.get_p_src()
    assert frozenset([(key, frozenset(col.items()))
                     for key, col in table.items()]) == expected


@pytest.mark.unit
@pytest.mark.ptables
@pytest.mark.parametrize('k, expected', [
    (0, frozenset([
        ('a1', frozenset([
            ('divert', 0),
            ('cancel:1', 0.5),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('a2', frozenset([
            ('divert', 1),
            ('cancel:1', 0.5),
            ('delay:1', 1),
            ('delay:2', 1)
        ])),
    ])),
    (1, frozenset([
        ('a1', frozenset([
            ('divert', 1 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 1 / 3),
            ('delay:2', 1 / 3)
        ])),
        ('a2', frozenset([
            ('divert', 2 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 2 / 3),
            ('delay:2', 2 / 3)
        ])),
    ]))
])
def test_fit_dst(k: int, expected: set[tuple[str, float]]):
    """Test fitting destination airport probabilities.

    k -- smoothing factor
    """
    tables = setup_ptables(k)

    # Check status counter
    table = tables.get_p_dst()
    assert frozenset([(key, frozenset(col.items()))
                     for key, col in table.items()]) == expected


@pytest.mark.unit
@pytest.mark.ptables
@pytest.mark.parametrize('k, expected', [
    (0, frozenset([
        ('0000', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0030', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0100', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0130', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0200', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0230', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0300', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0330', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0400', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0430', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0500', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0530', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0600', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0630', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0700', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0730', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0800', frozenset([
            ('divert', 1),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0830', frozenset([
            ('divert', 0),
            ('cancel:1', 0.5),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0900', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('0930', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1000', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1030', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1100', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1130', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1200', frozenset([
            ('divert', 0),
            ('cancel:1', 0.5),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1230', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1300', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1330', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1400', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 1),
            ('delay:2', 0)
        ])),
        ('1430', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 1)
        ])),
        ('1500', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1530', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1600', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1630', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1700', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1730', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1800', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1830', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1900', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('1930', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('2000', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('2030', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('2100', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('2130', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('2200', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('2230', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('2300', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('2330', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
    ])),
    (1, frozenset([
        ('0000', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0030', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0100', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0130', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0200', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0230', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0300', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0330', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0400', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0430', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0500', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0530', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0600', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0630', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0700', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0730', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0800', frozenset([
            ('divert', 2 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0830', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 2 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0900', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('0930', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1000', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1030', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1100', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1130', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1200', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 2 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1230', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1300', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1330', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1400', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 2 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1430', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 2 / 49)
        ])),
        ('1500', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1530', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1600', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1630', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1700', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1730', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1800', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1830', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1900', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('1930', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('2000', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('2030', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('2100', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('2130', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('2200', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('2230', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('2300', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
        ('2330', frozenset([
            ('divert', 1 / 49),
            ('cancel:1', 1 / 50),
            ('delay:1', 1 / 49),
            ('delay:2', 1 / 49)
        ])),
    ]))
])
def test_fit_dep_time(k: int, expected: set[tuple[str, float]]):
    """Test fitting departure time probabilities.

    k -- smoothing factor
    """
    tables = setup_ptables(k)

    # Check status counter
    table = tables.get_p_dep_time()
    assert frozenset([(key, frozenset(col.items()))
                     for key, col in table.items()]) == expected


@pytest.mark.unit
@pytest.mark.ptables
@pytest.mark.parametrize('k, expected', [
    (0, frozenset([
        (1, frozenset([
            ('divert', 1),
            ('cancel:1', 0.5),
            ('delay:1', 1),
            ('delay:2', 1)
        ])),
        (2, frozenset([
            ('divert', 0),
            ('cancel:1', 0.5),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
    ])),
    (1, frozenset([
        (1, frozenset([
            ('divert', 2 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 2 / 3),
            ('delay:2', 2 / 3)
        ])),
        (2, frozenset([
            ('divert', 1 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 1 / 3),
            ('delay:2', 1 / 3)
        ])),
    ]))
])
def test_fit_src_tmp(k: int, expected: set[tuple[str, float]]):
    """Test fitting source temperature probabilities.

    k -- smoothing factor
    """
    tables = setup_ptables(k)

    # Check status counter
    table = tables.get_p_src_tmp()
    assert frozenset([(key, frozenset(col.items()))
                     for key, col in table.items()]) == expected


@pytest.mark.unit
@pytest.mark.ptables
@pytest.mark.parametrize('k, expected', [
    (0, frozenset([
        (1, frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 1),
            ('delay:2', 1)
        ])),
        (2, frozenset([
            ('divert', 1),
            ('cancel:1', 1),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
    ])),
    (1, frozenset([
        (1, frozenset([
            ('divert', 1 / 3),
            ('cancel:1', 1 / 4),
            ('delay:1', 2 / 3),
            ('delay:2', 2 / 3)
        ])),
        (2, frozenset([
            ('divert', 2 / 3),
            ('cancel:1', 3 / 4),
            ('delay:1', 1 / 3),
            ('delay:2', 1 / 3)
        ])),
    ]))
])
def test_fit_dst_tmp(k: int, expected: set[tuple[str, float]]):
    """Test fitting destination temperature probabilities.

    k -- smoothing factor
    """
    tables = setup_ptables(k)

    # Check status counter
    table = tables.get_p_dst_tmp()
    assert frozenset([(key, frozenset(col.items()))
                     for key, col in table.items()]) == expected


@pytest.mark.unit
@pytest.mark.ptables
@pytest.mark.parametrize('k, expected', [
    (0, frozenset([
        (1, frozenset([
            ('divert', 1),
            ('cancel:1', 0.5),
            ('delay:1', 0),
            ('delay:2', 1)
        ])),
        (2, frozenset([
            ('divert', 0),
            ('cancel:1', 0.5),
            ('delay:1', 1),
            ('delay:2', 0)
        ])),
    ])),
    (1, frozenset([
        (1, frozenset([
            ('divert', 2 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 1 / 3),
            ('delay:2', 2 / 3)
        ])),
        (2, frozenset([
            ('divert', 1 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 2 / 3),
            ('delay:2', 1 / 3)
        ])),
    ]))
])
def test_fit_src_wnd(k: int, expected: set[tuple[str, float]]):
    """Test fitting source wind speed probabilities.

    k -- smoothing factor
    """
    tables = setup_ptables(k)

    # Check status counter
    table = tables.get_p_src_wnd()
    assert frozenset([(key, frozenset(col.items()))
                     for key, col in table.items()]) == expected


@pytest.mark.unit
@pytest.mark.ptables
@pytest.mark.parametrize('k, expected', [
    (0, frozenset([
        (1, frozenset([
            ('divert', 0),
            ('cancel:1', 0.5),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        (2, frozenset([
            ('divert', 1),
            ('cancel:1', 0.5),
            ('delay:1', 1),
            ('delay:2', 1)
        ])),
    ])),
    (1, frozenset([
        (1, frozenset([
            ('divert', 1 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 1 / 3),
            ('delay:2', 1 / 3)
        ])),
        (2, frozenset([
            ('divert', 2 / 3),
            ('cancel:1', 2 / 4),
            ('delay:1', 2 / 3),
            ('delay:2', 2 / 3)
        ])),
    ]))
])
def test_fit_dst_wnd(k: int, expected: set[tuple[str, float]]):
    """Test fitting destination wind speed probabilities.

    k -- smoothing factor
    """
    tables = setup_ptables(k)

    # Check status counter
    table = tables.get_p_dst_wnd()
    assert frozenset([(key, frozenset(col.items()))
                     for key, col in table.items()]) == expected
