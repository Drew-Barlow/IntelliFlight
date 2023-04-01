import pytest
import json
from pathlib import Path
from intelliflight.models.components.keymeta import KeyMeta
from intelliflight.models.components.dataset import Dataset
from intelliflight.models.components.frequencycounter import FrequencyCounter
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


def setup_counter():
    counter = FrequencyCounter()
    counter.reset_counters(get_keymeta())
    counter.count_frequencies(get_dataset())
    return counter


## TESTS ##


@pytest.mark.unit
@pytest.mark.frequencies
def test_reset_counters():
    """Test initialization of counter keys and values.
    Also tests `get_<x>_counter()` and `query_<x>_counter()`, which
    are used in the process of retrieving initialized values.
    """
    counter = FrequencyCounter()
    counter.reset_counters(get_keymeta())

    # Check status counter
    status_keys = {'divert', 'cancel:1', 'delay:1', 'delay:2'}
    assert set(counter.get_status_counter().keys()) == status_keys
    for key in status_keys:
        assert counter.query_status_counter(key) == 0

    # Check day counter
    day_keys = {'1', '2', '3', '4', '5', '6', '7'}
    day_counter = counter.get_day_counter()
    assert set(day_counter.keys()) == day_keys
    for key in day_keys:
        assert set(day_counter[key].keys()) == status_keys
        for status_k in status_keys:
            assert counter.query_day_counter(key, status_k) == 0

    # Check airline counter
    airline_keys = {'c1', 'c2'}
    airline_counter = counter.get_airline_counter()
    assert set(airline_counter.keys()) == airline_keys
    for key in airline_keys:
        assert set(airline_counter[key].keys()) == status_keys
        for status_k in status_keys:
            assert counter.query_airline_counter(key, status_k) == 0

    # Check src counter
    src_keys = {'a1', 'a2'}
    src_counter = counter.get_src_counter()
    assert set(src_counter.keys()) == src_keys
    for key in src_keys:
        assert set(src_counter[key].keys()) == status_keys
        for status_k in status_keys:
            assert counter.query_src_counter(key, status_k) == 0

    # Check dst counter
    dst_keys = src_keys
    dst_counter = counter.get_dst_counter()
    assert set(dst_counter.keys()) == dst_keys
    for key in dst_keys:
        assert set(dst_counter[key].keys()) == status_keys
        for status_k in status_keys:
            assert counter.query_dst_counter(key, status_k) == 0

    # Check dep_time counter
    dep_time_counter = counter.get_dep_time_counter()
    assert frozenset(dep_time_counter.keys()) == DEP_TIME_KEYS
    for key in DEP_TIME_KEYS:
        assert set(dep_time_counter[key].keys()) == status_keys
        for status_k in status_keys:
            assert counter.query_dep_time_counter(key, status_k) == 0

    # Check src_tmp counter
    src_tmp_keys = {1, 2}
    src_tmp_counter = counter.get_src_tmp_counter()
    assert set(src_tmp_counter.keys()) == src_tmp_keys
    for key in src_tmp_keys:
        assert set(src_tmp_counter[key].keys()) == status_keys
        for status_k in status_keys:
            assert counter.query_src_tmp_counter(key, status_k) == 0

    # Check dst_tmp counter
    dst_tmp_keys = src_tmp_keys
    dst_tmp_counter = counter.get_dst_tmp_counter()
    assert set(dst_tmp_counter.keys()) == dst_tmp_keys
    for key in dst_tmp_keys:
        assert set(dst_tmp_counter[key].keys()) == status_keys
        for status_k in status_keys:
            assert counter.query_dst_tmp_counter(key, status_k) == 0

    # Check src_wind counter
    src_wind_keys = {1, 2}
    src_wind_counter = counter.get_src_wind_counter()
    assert set(src_wind_counter.keys()) == src_wind_keys
    for key in src_wind_keys:
        assert set(src_wind_counter[key].keys()) == status_keys
        for status_k in status_keys:
            assert counter.query_src_wnd_counter(key, status_k) == 0

    # Check dst_wind counter
    dst_wind_keys = src_wind_keys
    dst_wind_counter = counter.get_dst_wind_counter()
    assert set(dst_wind_counter.keys()) == dst_wind_keys
    for key in dst_wind_keys:
        assert set(dst_wind_counter[key].keys()) == status_keys
        for status_k in status_keys:
            assert counter.query_dst_wnd_counter(key, status_k) == 0


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_statuses():
    """Test counting arrival statuses."""
    counter = setup_counter()

    # Check status counter
    status_counter = counter.get_status_counter()
    assert set(status_counter.items()) == {
        ('divert', 1),
        ('cancel:1', 2),
        ('delay:1', 1),
        ('delay:2', 1)
    }


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_days():
    """Test counting days per status."""
    counter = setup_counter()

    # Check day counter
    day_counter = counter.get_day_counter()
    assert frozenset([(key, frozenset(col.items())) for key, col in day_counter.items()]) == frozenset([
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
            ('cancel:1', 1),
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
            ('cancel:1', 1),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
    ])


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_airlines():
    """Test counting airlines per status."""
    counter = setup_counter()

    # Check day counter
    airline_counter = counter.get_airline_counter()
    assert frozenset([(key, frozenset(col.items())) for key, col in airline_counter.items()]) == frozenset([
        ('c1', frozenset([
            ('divert', 1),
            ('cancel:1', 1),
            ('delay:1', 1),
            ('delay:2', 1)
        ])),
        ('c2', frozenset([
            ('divert', 0),
            ('cancel:1', 1),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
    ])


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_src():
    """Test counting source airports per status."""
    counter = setup_counter()

    # Check day counter
    src_counter = counter.get_src_counter()
    assert frozenset([(key, frozenset(col.items())) for key, col in src_counter.items()]) == frozenset([
        ('a1', frozenset([
            ('divert', 1),
            ('cancel:1', 1),
            ('delay:1', 1),
            ('delay:2', 0)
        ])),
        ('a2', frozenset([
            ('divert', 0),
            ('cancel:1', 1),
            ('delay:1', 0),
            ('delay:2', 1)
        ])),
    ])


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_dst():
    """Test counting destination airports per status."""
    counter = setup_counter()

    # Check day counter
    dst_counter = counter.get_dst_counter()
    assert frozenset([(key, frozenset(col.items())) for key, col in dst_counter.items()]) == frozenset([
        ('a1', frozenset([
            ('divert', 0),
            ('cancel:1', 1),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        ('a2', frozenset([
            ('divert', 1),
            ('cancel:1', 1),
            ('delay:1', 1),
            ('delay:2', 1)
        ])),
    ])


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_dep_time():
    """Test counting departure times per status."""
    counter = setup_counter()

    # Check day counter
    dep_time_counter = counter.get_dep_time_counter()
    counter_items = frozenset([(key, frozenset(col.items()))
                              for key, col in dep_time_counter.items()])
    assert ('1400', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 1),
            ('delay:2', 0)
            ])) in counter_items
    assert ('1430', frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 1)
            ])) in counter_items
    assert ('1200', frozenset([
            ('divert', 0),
            ('cancel:1', 1),
            ('delay:1', 0),
            ('delay:2', 0)
            ])) in counter_items
    assert ('0800', frozenset([
            ('divert', 1),
            ('cancel:1', 0),
            ('delay:1', 0),
            ('delay:2', 0)
            ])) in counter_items
    assert ('0830', frozenset([
            ('divert', 0),
            ('cancel:1', 1),
            ('delay:1', 0),
            ('delay:2', 0)
            ])) in counter_items

    # Check all other times
    for key in [time for time in DEP_TIME_KEYS if time not in ['1400', '1430', '1200', '0800', '0830']]:
        assert (key, frozenset([
                ('divert', 0),
                ('cancel:1', 0),
                ('delay:1', 0),
                ('delay:2', 0)
                ])) in counter_items


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_src_tmp():
    """Test counting source temperatures per status."""

    counter = setup_counter()

    tmp_counter = counter.get_src_tmp_counter()
    assert frozenset([(key, frozenset(col.items())) for key, col in tmp_counter.items()]) == frozenset([
        (1, frozenset([
            ('divert', 1),
            ('cancel:1', 1),
            ('delay:1', 1),
            ('delay:2', 1)
        ])),
        (2, frozenset([
            ('divert', 0),
            ('cancel:1', 1),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
    ])


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_dst_tmp():
    """Test counting destination temperatures per status."""

    counter = setup_counter()

    tmp_counter = counter.get_dst_tmp_counter()
    assert frozenset([(key, frozenset(col.items())) for key, col in tmp_counter.items()]) == frozenset([
        (1, frozenset([
            ('divert', 0),
            ('cancel:1', 0),
            ('delay:1', 1),
            ('delay:2', 1)
        ])),
        (2, frozenset([
            ('divert', 1),
            ('cancel:1', 2),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
    ])


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_src_wnd():
    """Test counting source wind speeds per status."""

    counter = setup_counter()

    wnd_counter = counter.get_src_wind_counter()
    assert frozenset([(key, frozenset(col.items())) for key, col in wnd_counter.items()]) == frozenset([
        (1, frozenset([
            ('divert', 1),
            ('cancel:1', 1),
            ('delay:1', 0),
            ('delay:2', 1)
        ])),
        (2, frozenset([
            ('divert', 0),
            ('cancel:1', 1),
            ('delay:1', 1),
            ('delay:2', 0)
        ])),
    ])


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_dst_wnd():
    """Test counting destination wind speeds per status."""

    counter = setup_counter()

    wnd_counter = counter.get_dst_wind_counter()
    assert frozenset([(key, frozenset(col.items())) for key, col in wnd_counter.items()]) == frozenset([
        (1, frozenset([
            ('divert', 0),
            ('cancel:1', 1),
            ('delay:1', 0),
            ('delay:2', 0)
        ])),
        (2, frozenset([
            ('divert', 1),
            ('cancel:1', 1),
            ('delay:1', 1),
            ('delay:2', 1)
        ])),
    ])


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_statuses_with_test_part():
    """Test counting arrival statuses with a test partition."""
    counter = FrequencyCounter()
    counter.reset_counters(get_keymeta())
    dataset = get_dataset()
    dataset.set_test_bounds(0, 1)
    counter.count_frequencies(dataset)

    # Check status counter
    status_counter = counter.get_status_counter()
    assert set(status_counter.items()) == {
        ('divert', 1),
        ('cancel:1', 2),
        ('delay:1', 0),
        ('delay:2', 1)
    }


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_statuses_with_both_parts():
    """Test counting arrival statuses with a test and validation partition
    partition."""
    counter = FrequencyCounter()
    counter.reset_counters(get_keymeta())
    dataset = get_dataset()
    dataset.set_test_bounds(0, 1)
    dataset.set_validation_bounds(1, 2)
    counter.count_frequencies(dataset)

    # Check status counter
    status_counter = counter.get_status_counter()
    assert set(status_counter.items()) == {
        ('divert', 1),
        ('cancel:1', 2),
        ('delay:1', 0),
        ('delay:2', 0)
    }


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_statuses_with_validation_no_test():
    """Attempt to count arrival statuses with a validation partition but no
    test partition."""
    counter = FrequencyCounter()
    counter.reset_counters(get_keymeta())
    dataset = get_dataset()
    dataset.set_validation_bounds(1, 2)

    with pytest.raises(TypeError):
        counter.count_frequencies(dataset)


@pytest.mark.unit
@pytest.mark.frequencies
def test_count_uninitialized():
    """Attempt to count frequencies with uninitialized counters."""
    with pytest.raises(BufferError):
        FrequencyCounter().count_frequencies(get_dataset())
