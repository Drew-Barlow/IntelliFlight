from copy import deepcopy
from intelliflight.models.components.dataset import Dataset
from intelliflight.models.components.keymeta import KeyMeta


class FrequencyCounter:
    def __init__(self):
        # Frequency dicts. These store the frequency of variables
        # in the training data and are used to generate probability values.
        self.__status_counter: dict[str, int] = None
        self.__day_counter: dict[str, dict[str, int]] = None
        self.__airline_counter: dict[str, dict[str, int]] = None
        self.__src_counter: dict[str, dict[str, int]] = None
        self.__dst_counter: dict[str, dict[str, int]] = None
        self.__dep_time_counter: dict[str, dict[str, int]] = None
        self.__src_tmp_counter: dict[str, dict[str, int]] = None
        self.__dst_tmp_counter: dict[str, dict[str, int]] = None
        self.__src_wind_counter: dict[str, dict[str, int]] = None
        self.__dst_wind_counter: dict[str, dict[str, int]] = None
        self.__counters_reset: bool = False

    def reset_counters(self, key_meta: KeyMeta):
        # Reset frequency counters
        self.__status_counter = {
            key: 0 for key in key_meta.get_status_keys()}

        self.__day_counter = {str(day_k): self.__status_counter.copy()
                              for day_k in range(1, 8)}

        self.__airline_counter = {aline_k: self.__status_counter.copy()
                                  for aline_k in key_meta.get_seen_carriers()}

        self.__src_counter = {src_k: self.__status_counter.copy()
                              for src_k in key_meta.get_seen_airports()}

        self.__dst_counter = deepcopy(self.__src_counter)

        self.__dep_time_counter = {dep_k: self.__status_counter.copy()
                                   for dep_k in key_meta.get_dep_times()}

        self.__src_tmp_counter = {tmp_k: self.__status_counter.copy()
                                  for tmp_k in key_meta.get_temp_keys()}

        self.__dst_tmp_counter = deepcopy(self.__src_tmp_counter)

        self.__src_wind_counter = {wnd_k: self.__status_counter.copy()
                                   for wnd_k in key_meta.get_wind_keys()}

        self.__dst_wind_counter = deepcopy(self.__src_wind_counter)

        self.__counters_reset = True

    def count_frequencies(self, dataset: Dataset):
        # Error checking
        if not self.__counters_reset:
            raise BufferError(
                'FrequencyCounter: ERR: Counters were not reset. Run reset_counters() first.')
        validation_start, validation_end = dataset.get_validation_bounds()
        test_start, test_end = dataset.get_test_bounds()
        # Validation bounds must both be None or both have values
        if (validation_start is None) != (validation_end is None):
            raise TypeError(
                f'FrequencyCounter.count_frequencies(): Provided validation_start={validation_start} and validation_end={validation_end} (Either both or neither must be None).')
        elif validation_start is None:
            # Test bounds must both be None or both have values
            if (test_start is None) != (test_end is None):
                raise TypeError(
                    f'FrequencyCounter.count_frequencies(): Provided test_start={test_start} and test_end={test_end} (Either both or neither must be None).')
            # If there is no test set, make the bounds negative so the index in the dataset never falls between them
            if test_start is None:
                test_start = -999
                test_end = -999
            # test_end must come after test_start
            elif test_start > test_end:
                raise ValueError(
                    f'FrequencyCounter.count_frequencies(): test_start={test_start} > test_end={test_end}')
            # Set bounds to test set bounds
            validation_start = test_start
            validation_end = test_end
        else:
            # Cannot have validation set but no test set
            if test_start is None or test_end is None:
                raise TypeError(
                    'FrequencyCounter.count_frequencies(): Test set boundaries cannot be None if a validation set is defined.')
            # test_end must come after test_start
            if test_start > test_end:
                raise ValueError(
                    f'FrequencyCounter.count_frequencies(): test_start={test_start} > test_end={test_end}')
            # validation_end must come after validation_start
            if validation_start > validation_end:
                raise ValueError(
                    f'FrequencyCounter.count_frequencies(): validation_start={validation_start} > validation_end={validation_end}')

        data = dataset.get_data()
        # Count variables
        for i in range(dataset.get_len()):
            # Check if record is in test or validation set
            if ((test_start <= i < test_end)
                    or (validation_start <= i < validation_end)):
                continue
            record = data[i]
            # Process arrival status
            status_k = None
            if record['CANCELLED'] == '1.00':
                status_k = f'cancel:{record["CANCELLATION_CODE"]}'
            elif record['DIVERTED'] == '1.00':
                status_k = 'divert'
            else:
                status_k = f'delay:{record["ARR_DELAY_GROUP"]}'

            self.__status_counter[status_k] += 1

            # Process other variables
            self.__day_counter[record['DAY_OF_WEEK']][status_k] += 1
            self.__airline_counter[record['OP_UNIQUE_CARRIER']
                                   ][status_k] += 1
            self.__src_counter[record['ORIGIN_AIRPORT_ID']
                               ][status_k] += 1
            self.__dst_counter[record['DEST_AIRPORT_ID']][status_k] += 1
            self.__dep_time_counter[record['CRS_DEP_TIME']
                                    ][status_k] += 1
            self.__src_tmp_counter[record['src_tavg']][status_k] += 1
            self.__dst_tmp_counter[record['dst_tavg']][status_k] += 1
            self.__src_wind_counter[record['src_wspd']][status_k] += 1
            self.__dst_wind_counter[record['dst_wspd']][status_k] += 1

        self.__counters_reset = False

    def get_status_counter(self) -> dict[str, int]:
        return self.__status_counter.copy()

    def get_day_counter(self) -> dict[str, dict[str, int]]:
        return deepcopy(self.__day_counter)

    def get_airline_counter(self) -> dict[str, dict[str, int]]:
        return deepcopy(self.__airline_counter)

    def get_src_counter(self) -> dict[str, dict[str, int]]:
        return deepcopy(self.__src_counter)

    def get_dst_counter(self) -> dict[str, dict[str, int]]:
        return deepcopy(self.__dst_counter)

    def get_dep_time_counter(self) -> dict[str, dict[str, int]]:
        return deepcopy(self.__dep_time_counter)

    def get_src_tmp_counter(self) -> dict[str, dict[str, int]]:
        return deepcopy(self.__src_tmp_counter)

    def get_dst_tmp_counter(self) -> dict[str, dict[str, int]]:
        return deepcopy(self.__dst_tmp_counter)

    def get_src_wind_counter(self) -> dict[str, dict[str, int]]:
        return deepcopy(self.__src_wind_counter)

    def get_dst_wind_counter(self) -> dict[str, dict[str, int]]:
        return deepcopy(self.__dst_wind_counter)

    def query_status_counter(self, status: str) -> int:
        return self.__status_counter[status]

    def query_day_counter(self, day: str, status: str) -> int:
        return self.__day_counter[day][status]

    def query_airline_counter(self, airline: str, status: str) -> int:
        return self.__airline_counter[airline][status]

    def query_src_counter(self, src: str, status: str) -> int:
        return self.__src_counter[src][status]

    def query_dst_counter(self, dst: str, status: str) -> int:
        return self.__dst_counter[dst][status]

    def query_dep_time_counter(self, dep_time: str, status: str) -> int:
        return self.__dep_time_counter[dep_time][status]

    def query_src_tmp_counter(self, src_tmp: str, status: str) -> int:
        return self.__src_tmp_counter[src_tmp][status]

    def query_dst_tmp_counter(self, dst_tmp: str, status: str) -> int:
        return self.__dst_tmp_counter[dst_tmp][status]

    def query_src_wnd_counter(self, src_wnd: str, status: str) -> int:
        return self.__src_wind_counter[src_wnd][status]

    def query_dst_wnd_counter(self, dst_wnd: str, status: str) -> int:
        return self.__dst_wind_counter[dst_wnd][status]
