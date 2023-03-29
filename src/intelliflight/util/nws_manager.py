import requests
import json
import datetime
from typing import Final
from schema import Schema, And
from intelliflight.util import typeutil

from ..util import DATA_PATH


class Forecaster:
    NWS_POINTS_ENDPOINT: Final = 'https://api.weather.gov/points/{lat},{lon}'
    AIRPORT_MAP_SCHEMA: Final = Schema([
        {
            "desc": str,
            "icao": And(str, lambda s: len(s) == 4),
            "faa": And(str, lambda s: len(s) == 3),
            "mstat": And(str, lambda s: typeutil.is_int(s)),
            "location": {
                "lat": And(str, lambda s: typeutil.is_float(s)),
                "lon": And(str, lambda s: typeutil.is_float(s))
            },
            "bts_id": And(str, lambda s: typeutil.is_int(s))
        }
    ])

    def __init__(self, map_path: str, http_get: callable = requests.get):
        """Initialize Forecaster with airport mappings and a GET function.

        Positional arguments:

        map_path -- Path to an airport mappings file of schema
                    `Forecaster.AIRPORT_MAP_SCHEMA`.
        http_get -- Function returning a `requests.Response`-like object.
                    Useful for dependency injection for testing. Defaults to
                    requests.get().
        """
        self.http_get = http_get
        with open(map_path, 'r') as f_mappings:
            self.AIRPORT_MAPPINGS = json.load(f_mappings)
        # Validate that mapping schema is valid
        Forecaster.AIRPORT_MAP_SCHEMA.validate(self.AIRPORT_MAPPINGS)

        print(f'{__name__}: Initialized weather API module')

    # Documentation for NWS forecast API is here:
    # https://weather-gov.github.io/api/general-faqs

    def get_nws_forecast_from_bts(self, bts_id: int, iso_timestamp: str) -> dict:
        """Given an airport BTS ID and time, return a National Weather Forecast.
        Parameters:
        bts_id -- The BTS ID of an airport.
        iso_timestamp -- An ISO-formatted timestamp of time for which a forecast
                        should be recieved. Can be no more than 7 days in the future.

        Returns:
        A dictionary containing forecast data for the hour containing iso_timestamp.
        A sample output can be found here: https://api.weather.gov/gridpoints/LWX/96,70/forecast/hourly
        (The returned values is one of the objects under ['properties']['periods']).

        Exceptions:
        ConnectionError -- Raised if the API request to NWS fails.
        KeyError -- Raised if the requested BTS ID is not in the mappings file.
        ValueError -- Raised if iso_timestamp is not in range (now, now + 7 days).
        """

        # Validate timestamp format
        if iso_timestamp[-1] == 'Z':
            iso_timestamp = iso_timestamp[:-1]

        for airport in self.AIRPORT_MAPPINGS:
            # Find BTS ID in known airports
            if int(airport['bts_id']) == bts_id:
                # Given lat/lon of airport, get the corresponding forecast area
                # from National Weather Service
                point_res: requests.Response = self.http_get(Forecaster.NWS_POINTS_ENDPOINT.format(lat=round(
                    float(airport['location']['lat']), 4), lon=round(float(airport['location']['lon']), 4)))

                if point_res.status_code != 200:
                    raise ConnectionError(
                        f'NWS point lookup returned {point_res.status_code}: {point_res.text}')

                # Get hourly forecast for the next 7 days using URL provided
                # in the previous API response's body
                hourly_res: requests.Response = self.http_get(
                    point_res.json()['properties']['forecastHourly'])

                if hourly_res.status_code != 200:
                    raise ConnectionError(
                        f'NWS forecast lookup returned {hourly_res.status_code}: {hourly_res.text}')

                # From all 1-hour periods in the forecast, find and return
                # the one containing iso_timestamp
                requested_timestamp = datetime.datetime.fromisoformat(
                    iso_timestamp)
                for period in hourly_res.json()['properties']['periods']:
                    start_time = datetime.datetime.fromisoformat(
                        period['startTime'])
                    end_time = datetime.datetime.fromisoformat(
                        period['endTime'])

                    if start_time.timestamp() <= requested_timestamp.timestamp() < end_time.timestamp():
                        return period

                raise ValueError(
                    f'Timestamp {iso_timestamp} is outside the allowed range.')

        # Provided airport is unknown
        raise KeyError(f'No airport with BTS ID {bts_id} found in mappings.')


# if __name__ == '__main__':
#     # Simple test case for Detroit Metro Airport
#     print(json.dumps(Forecaster(f'{DATA_PATH}/maps/airport_mappings.json').get_nws_forecast_from_bts(
#         10170, datetime.datetime.now().isoformat()), indent=2))
