from typing import Final

# Key values for weather data in historical data and NWS weather forecasts
WEATHER_FIELDS: Final = [
    {
        'historical': 'tavg',
        'forecast': 'temperature'
    },
    {
        'historical': 'wspd',
        'forecast': 'windSpeed'
    }
]

TIME_INTERVAL_SIZE: Final = 30  # minutes
