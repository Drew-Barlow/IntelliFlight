"""Utility functions for type checking"""

from schema import Schema, And
from typing import Final

AIRPORT_MAP_SCHEMA: Final = Schema([
    {
        "desc": str,
        "icao": And(str, lambda s: len(s) == 4),
        "faa": And(str, lambda s: len(s) == 3),
        "mstat": str,
        "location": {
            "lat": And(str, lambda s: is_float(s)),
            "lon": And(str, lambda s: is_float(s))
        },
        "bts_id": And(str, lambda s: is_int(s))
    }
])


def is_float(val: str) -> bool:
    """Test whether string `val` is a float"""
    try:
        float(val)
        return True
    except ValueError:
        return False


def is_int(val: str) -> bool:
    """Test whether string `val` is an int"""
    try:
        int(val)
        return True
    except ValueError:
        return False
