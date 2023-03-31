import pytest
import json
from pathlib import Path
from schema import SchemaError
import intelliflight.util.nws_manager as nws
from typing import Final
from datetime import datetime

TEST_PATH: Final = Path(__file__).parent.parent
VALID_MAP_PATH: Final = TEST_PATH / "data" / "valid_airport_mappings.json"
BAD_MAP_PATH: Final = TEST_PATH / 'data' / 'bad_airport_mappings.json'


class HttpResponseDummy:
    """Dummy class for mocking requests.Response.
    Implements .status_code, .text, and .json()."""

    def __init__(self, status_code: int, text: str, json_data):
        self.status_code = status_code
        self.text = text
        self.__json_data = json_data

    def json(self):
        return self.__json_data


def generate_get_func(endpoints: list) -> callable:
    """"""
    def get_f(url: str, *args):
        for endpoint in endpoints:
            if url.find(endpoint['url']) == 0:
                return endpoint['res']
    return get_f


def get_bad_mappings():
    bad_map_cases = json.load(BAD_MAP_PATH.open('r'))
    return [tuple(case) for case in bad_map_cases]


@pytest.mark.unit
@pytest.mark.nws
def test_init_bad_mapping_path():
    with pytest.raises(FileNotFoundError):
        nws.Forecaster('BAD_PATH')


@pytest.mark.unit
@pytest.mark.nws
@pytest.mark.parametrize("comment, bad_mapping", get_bad_mappings())
def test_init_bad_mapping_json(tmp_path: Path, comment: str, bad_mapping: dict):
    # comment arg is printed if the test fails and is helpful for debugging.
    tmp_map_path = tmp_path / 'nws_bad_mapping.json'
    tmp_map_path.write_text(json.dumps([bad_mapping]))
    bad_json_path = TEST_PATH.joinpath(tmp_map_path)
    with pytest.raises(SchemaError):
        nws.Forecaster(bad_json_path.as_posix())


@pytest.mark.unit
@pytest.mark.nws
def test_init_valid_mapping():
    forecaster = nws.Forecaster(VALID_MAP_PATH.as_posix())
    assert forecaster.AIRPORT_MAPPINGS == json.load(VALID_MAP_PATH.open())


@pytest.mark.unit
@pytest.mark.nws
def test_forecast_out_of_bounds_bts_id():
    with pytest.raises(KeyError):
        timestamp = datetime.now().isoformat()
        nws.Forecaster(VALID_MAP_PATH.as_posix()
                       ).get_nws_forecast_from_bts(-1, timestamp)


@pytest.mark.unit
@pytest.mark.nws
def test_forecast_points_get_error():
    res_dummy = HttpResponseDummy(500, 'Error 500', None)
    with pytest.raises(ConnectionError):
        forecaster = nws.Forecaster(
            VALID_MAP_PATH.as_posix(),
            generate_get_func([{
                'url': nws.Forecaster.NWS_POINTS_ENDPOINT.split('{')[0],
                'res': res_dummy
            }])
        )
        forecaster.get_nws_forecast_from_bts(10135, datetime.now().isoformat())


@pytest.mark.unit
@pytest.mark.nws
def test_forecast_hourly_get_error():
    hourly_url = 'hourlyURL'
    point_res = HttpResponseDummy(200, '', {
        'properties': {
            'forecastHourly': hourly_url
        }
    })
    hourly_res = HttpResponseDummy(500, 'Error 500', None)
    with pytest.raises(ConnectionError):
        forecaster = nws.Forecaster(
            VALID_MAP_PATH.as_posix(),
            generate_get_func([
                {
                    'url': nws.Forecaster.NWS_POINTS_ENDPOINT.split('{')[0],
                    'res': point_res
                },
                {
                    'url': hourly_url,
                    'res': hourly_res
                }
            ])
        )
        forecaster.get_nws_forecast_from_bts(10135, datetime.now().isoformat())


@pytest.mark.unit
@pytest.mark.nws
def test_forecast_invalid_timestamp():
    hourly_url = 'hourlyURL'
    point_res = HttpResponseDummy(200, '', {
        'properties': {
            'forecastHourly': hourly_url
        }
    })
    hourly_res = HttpResponseDummy(200, '', None)
    with pytest.raises(ValueError):
        forecaster = nws.Forecaster(
            VALID_MAP_PATH.as_posix(),
            generate_get_func([
                {
                    'url': nws.Forecaster.NWS_POINTS_ENDPOINT.split('{')[0],
                    'res': point_res
                },
                {
                    'url': hourly_url,
                    'res': hourly_res
                }
            ])
        )
        forecaster.get_nws_forecast_from_bts(10135, 'BAD_TIMESTAMP')


@pytest.mark.unit
@pytest.mark.nws
def test_forecast_out_of_bounds_timestamp():
    hourly_url = 'hourlyURL'
    point_res = HttpResponseDummy(200, '', {
        'properties': {
            'forecastHourly': hourly_url
        }
    })
    hourly_res = HttpResponseDummy(200, '', {
        'properties': {
            'periods': [{
                'startTime': '2023-01-01T00:00:00.000',
                'endTime': '2023-01-01T23:59:00.000'
            }]
        }
    })
    with pytest.raises(ValueError):
        forecaster = nws.Forecaster(
            VALID_MAP_PATH.as_posix(),
            generate_get_func([
                {
                    'url': nws.Forecaster.NWS_POINTS_ENDPOINT.split('{')[0],
                    'res': point_res
                },
                {
                    'url': hourly_url,
                    'res': hourly_res
                }
            ])
        )
        forecaster.get_nws_forecast_from_bts(10135, datetime.now().isoformat())


@pytest.mark.unit
@pytest.mark.nws
def test_forecast_valid():
    hourly_url = 'hourlyURL'
    point_res = HttpResponseDummy(200, '', {
        'properties': {
            'forecastHourly': hourly_url
        }
    })
    forecast_period = {
        'startTime': '2023-01-01T00:00:00.000',
        'endTime': '2023-01-01T23:59:00.000'
    }
    hourly_res = HttpResponseDummy(200, '', {
        'properties': {
            'periods': [forecast_period]
        }
    })
    forecaster = nws.Forecaster(
        VALID_MAP_PATH.as_posix(),
        generate_get_func([
            {
                'url': nws.Forecaster.NWS_POINTS_ENDPOINT.split('{')[0],
                'res': point_res
            },
            {
                'url': hourly_url,
                'res': hourly_res
            }
        ])
    )
    nws_forecast = forecaster.get_nws_forecast_from_bts(
        10135, '2023-01-01T12:00:00.000Z')
    assert nws_forecast == forecast_period
