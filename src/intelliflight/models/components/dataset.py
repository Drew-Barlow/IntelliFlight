class Dataset:
    """Stores the following:

    - A list of data
    - Length of stored dataset
    - Bounds of test partition (start inclusive, end exclusive)
    - Bounds of validation partition (start inclusive, end exclusive)
    """

    def __init__(self):
        self.__data: list = None
        self.__datalen: int = None
        self.__test_start: int = None
        self.__test_end: int = None
        self.__validation_start = None
        self.__validation_end = None

    def get_data(self) -> list:
        """Get data. This is NOT a copy; rather, it is a reference to this
        object's internal data list."""
        if self.__data is None:
            raise ValueError('Dataset: ERR: Data is None.')
        return self.__data

    def get_len(self) -> int:
        """Get length of full dataset."""
        if self.__datalen is None:
            raise ValueError('Dataset: ERR: Data is None.')
        return self.__datalen

    def get_training_len(self) -> int:
        """Get length of dataset, excluding test and validation partitions."""
        if self.__datalen is None:
            raise ValueError('Dataset: ERR: Data is None.')
        length = self.__datalen
        if self.__test_start is not None:
            length -= self.__test_end - self.__test_start

        if self.__validation_start is not None:
            length -= self.__validation_end - self.__validation_start

        return length

    def get_test_bounds(self) -> tuple[int, int]:
        """Get `(test_start, test_end)`"""
        return (self.__test_start, self.__test_end)

    def get_validation_bounds(self) -> tuple[int, int]:
        """Get `(validation_start, validation_end)`"""
        return (self.__validation_start, self.__validation_end)

    def set_data(self, data: list):
        """Set data. For performance, the data is NOT copied; changes to the
        passed list will affect this object's internal list."""
        self.__data = data
        self.__datalen = len(data)

    def set_test_bounds(self, test_start: int, test_end: int):
        """Set test partition bounds. Start is inclusive; end is exclusive."""
        if test_start >= test_end:
            raise ValueError('Dataset: ERR: test_start={} must be less than test_end={}'.format(
                test_start, test_end))
        self.__test_start = test_start
        self.__test_end = test_end

    def set_validation_bounds(self, validation_start: int, validation_end: int):
        """Set validation partition bounds.
        Start is inclusive; end is exclusive."""
        if validation_start >= validation_end:
            raise ValueError('Dataset: ERR: validation_start={} must be less than validation_end={}'.format(
                validation_start, validation_end))
        self.__validation_start = validation_start
        self.__validation_end = validation_end

    def clear_test_partition(self):
        """Set test bounds to `None`"""
        self.__test_start = None
        self.__test_end = None

    def clear_validation_partition(self):
        """Set validation bounds to `None`"""
        self.__validation_start = None
        self.__validation_end = None
