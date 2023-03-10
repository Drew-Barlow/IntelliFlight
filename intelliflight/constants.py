from typing import Final

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
