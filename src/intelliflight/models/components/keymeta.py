class KeyMeta:
    """Stores the following information:

    - Airport bts_id values in training data
    - Carrier codes in training data
    - Arrival statuses as `{ key: description }` (both `str`)
    - Key values for temperature buckets
    - Key values for wind speed buckets
    """

    def __init__(self):
        # Key values for possible arrival states:
        # -Arrived at destination (ahead, on-time, or delayed) [delay:<code>]
        # -Cancelled [cancel:<code>]
        # -Diverted to another airport [divert]
        self.__arrival_statuses: dict[str, str] = None
        self.__seen_airports: set[str] = None
        self.__seen_carriers: set[str] = None
        self.__temp_keys: list[str] = None
        self.__wind_keys: list[str] = None

        # Generate values for departure time buckets. Format:
        # [ '0000', '0030', '0100', ..., '2300', '2330' ]
        self.__DEP_TIMES: list[str] = []
        for i in range(24):
            for j in ['00', '30']:
                self.__DEP_TIMES.append(f'{str(i).rjust(2, "0")}{j}')

    def in_seen_airports(self, airport: str) -> bool:
        if self.__seen_airports is None:
            raise BufferError('KeyMeta: ERR: seen_airports not initialized.')
        return airport in self.__seen_airports

    def in_seen_carriers(self, airport: str) -> bool:
        if self.__seen_carriers is None:
            raise BufferError('KeyMeta: ERR: seen_carriers not initialized.')
        return airport in self.__seen_carriers

    def in_temp_keys(self, airport: str) -> bool:
        if self.__temp_keys is None:
            raise BufferError('KeyMeta: ERR: temp_keys not initialized.')
        return airport in self.__temp_keys

    def in_wind_keys(self, airport: str) -> bool:
        if self.__wind_keys is None:
            raise BufferError('KeyMeta: ERR: wind_keys not initialized.')
        return airport in self.__wind_keys

    def get_arrival_statuses(self) -> dict[str, str]:
        return self.__arrival_statuses.copy()

    def get_seen_airports(self) -> set[str]:
        return self.__seen_airports.copy()

    def get_seen_carriers(self) -> set[str]:
        return self.__seen_carriers.copy()

    def get_dep_times(self) -> list[str]:
        return self.__DEP_TIMES.copy()

    def get_temp_keys(self) -> list[str]:
        return self.__temp_keys.copy()

    def get_wind_keys(self) -> list[str]:
        return self.__wind_keys.copy()

    def get_status_keys(self) -> list[str]:
        return self.__arrival_statuses.keys()

    def set_arrival_statuses(self, arrival_statuses: dict[str, str]):
        self.__arrival_statuses = arrival_statuses.copy()

    def set_seen_airports(self, seen_airports: set[str]):
        self.__seen_airports = seen_airports.copy()

    def set_seen_carriers(self, seen_carriers: set[str]):
        self.__seen_carriers = seen_carriers.copy()

    def set_temp_keys(self, temp_keys: list[str]):
        self.__temp_keys = temp_keys.copy()

    def set_wind_keys(self, wind_keys: list[str]):
        self.__wind_keys = wind_keys.copy()
