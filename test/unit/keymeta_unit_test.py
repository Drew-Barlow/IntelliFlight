import pytest
from intelliflight.models.components.keymeta import KeyMeta


## HELPERS ##


def setup() -> KeyMeta:
    """Instantiate and return a KeyMeta object."""
    keymeta = KeyMeta()
    keymeta.set_arrival_statuses({
        's1': 'desc1',
        's2': 'desc2'
    })
    keymeta.set_seen_airports({'a1', 'a2'})
    keymeta.set_seen_carriers({'c1', 'c2'})
    keymeta.set_temp_keys(['t1', 't2'])
    keymeta.set_wind_keys(['w1', 'w2'])
    return keymeta


## TESTS ##


@pytest.mark.unit
@pytest.mark.keymeta
@pytest.mark.parametrize('airport, expected', [
    ('a1', True),
    ('a0', False)
])
def test_in_seen_airports(airport: str, expected: bool):
    """Test whether presence or absence in `seen_airports` is correctly
    detected."""
    assert setup().in_seen_airports(airport) == expected


@pytest.mark.unit
@pytest.mark.keymeta
@pytest.mark.parametrize('carrier, expected', [
    ('c1', True),
    ('c0', False)
])
def test_in_seen_carriers(carrier: str, expected: bool):
    """Test whether presence or absence in `seen_carriers` is correctly
    detected."""
    assert setup().in_seen_carriers(carrier) == expected


@pytest.mark.unit
@pytest.mark.keymeta
@pytest.mark.parametrize('temp_key, expected', [
    ('t1', True),
    ('t0', False)
])
def test_in_temp_keys(temp_key: str, expected: bool):
    """Test whether presence or absence in `temp_keys` is correctly
    detected."""
    assert setup().in_temp_keys(temp_key) == expected


@pytest.mark.unit
@pytest.mark.keymeta
@pytest.mark.parametrize('wind_key, expected', [
    ('w1', True),
    ('w0', False)
])
def test_in_wind_keys(wind_key: str, expected: bool):
    """Test whether presence or absence in `wind_keys` is correctly
    detected."""
    assert setup().in_wind_keys(wind_key) == expected


@pytest.mark.unit
@pytest.mark.keymeta
def test_get_dep_times():
    assert set(setup().get_dep_times()) == {
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
    }


@pytest.mark.unit
@pytest.mark.keymeta
def test_in_seen_airports_uninitialized():
    """Attempt to call in_seen_airports when that structure is `None`."""
    with pytest.raises(BufferError):
        KeyMeta().in_seen_airports('')


@pytest.mark.unit
@pytest.mark.keymeta
def test_in_seen_carriers_uninitialized():
    """Attempt to call in_seen_carriers when that structure is `None`."""
    with pytest.raises(BufferError):
        KeyMeta().in_seen_carriers('')


@pytest.mark.unit
@pytest.mark.keymeta
def test_in_temp_keys_uninitialized():
    """Attempt to call in_temp_keys when that structure is `None`."""
    with pytest.raises(BufferError):
        KeyMeta().in_temp_keys('')


@pytest.mark.unit
@pytest.mark.keymeta
def test_in_wind_keys_uninitialized():
    """Atwindt to call in_wind_keys when that structure is `None`."""
    with pytest.raises(BufferError):
        KeyMeta().in_wind_keys('')
