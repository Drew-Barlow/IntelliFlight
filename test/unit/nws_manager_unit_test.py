import pytest
import json
from pathlib import Path
from schema import SchemaError
import intelliflight.util.nws_manager as nws
from typing import Final
from datetime import datetime


## DATA ##


TEST_PATH: Final = Path(__file__).parent.parent
VALID_MAP_PATH: Final = TEST_PATH / "data" / "valid_airport_mappings.json"
BAD_MAP_PATH: Final = TEST_PATH / 'data' / 'bad_airport_mappings.json'


# HELPERS


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
    """Generate a function to mock `requests.get()`, returning predefined
    responses.

    Positional arguments:

    - endpoints -- list of urls the function accepts and corresponding
                   responses. Has the following schema:

                   [
                     {
                       'url': `str`
                       'res': `HttpResponseDummy`
                     },
                     ...
                   ]

    Returns:

    function with signature `f(url: str, *args)` and the following properties:

    - If `url` begins with one of the predefined addresses in `endpoints`, then
      return the corresponding response.
    - Else, return an `HttpResponseDummy` with status 404.
    """
    def get_f(url: str, *args):
        for endpoint in endpoints:
            # Check if a preset URL is a prefix of the input
            if url.find(endpoint['url']) == 0:
                return endpoint['res']

        return HttpResponseDummy(404, f'URL {url} not found', None)

    return get_f


def get_bad_mappings():
    """Parse `bad_airport_mappings.json` into a list of
    (comment, mapping) pairs."""
    bad_map_cases = json.load(BAD_MAP_PATH.open('r'))
    return [tuple(case) for case in bad_map_cases]


## TESTS ##


@pytest.mark.unit
@pytest.mark.nws
def test_init_bad_mapping_path():
    """Attempt to construct a Forecaster with a nonexistent mappings file."""
    with pytest.raises(FileNotFoundError):
        nws.Forecaster('BAD_PATH')


@pytest.mark.unit
@pytest.mark.nws
@pytest.mark.parametrize("comment, bad_mapping", get_bad_mappings())
def test_init_bad_mapping_json(tmp_path: Path, comment: str, bad_mapping: dict):
    """Attempt to construct a Forecaster with a malformed mapping file."""
    # comment arg is printed if the test fails and is helpful for debugging.

    # Dump bad mapping to a temporary file
    tmp_map_path = tmp_path / 'nws_bad_mapping.json'
    tmp_map_path.write_text(json.dumps([bad_mapping]))
    # Construct a Forecaster with the temporary file's path
    bad_json_path = TEST_PATH.joinpath(tmp_map_path)
    with pytest.raises(SchemaError):
        nws.Forecaster(bad_json_path.as_posix())


@pytest.mark.unit
@pytest.mark.nws
def test_init_valid_mapping():
    """Verify that airport mappings are loaded correctly."""
    forecaster = nws.Forecaster(VALID_MAP_PATH.as_posix())
    assert forecaster.AIRPORT_MAPPINGS == json.load(VALID_MAP_PATH.open())


@pytest.mark.unit
@pytest.mark.nws
def test_forecast_out_of_bounds_bts_id():
    """Attempt to get weather for an unknown airport."""
    with pytest.raises(KeyError):
        timestamp = datetime.now().isoformat()
        nws.Forecaster(VALID_MAP_PATH.as_posix()
                       ).get_nws_forecast_from_bts(-1, timestamp)


@pytest.mark.unit
@pytest.mark.nws
def test_forecast_points_get_error():
    """Verify behavior if the NWS points endpoint is down (error 500)."""
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
    """Verify behavior if the NWS forecast endpoint is down (error 500)."""
    hourly_url = 'hourlyURL'
    # The content of this response is irrelevant since we control the response
    # from the mock forecast endpoint.
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
    """Attempt to get a weather forecast for an invalid timestamp."""
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
    """Attempt to get weather for a timestamp not covered in forecast data."""
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
    """Verify that forecasts are correctly retrieved for valid input."""
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
