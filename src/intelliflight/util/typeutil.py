"""Utility functions for type checking"""


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
