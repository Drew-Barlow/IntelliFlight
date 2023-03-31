from copy import deepcopy
from intelliflight.models.components.dataset import Dataset
from intelliflight.models.components.keymeta import KeyMeta
from intelliflight.models.components.frequencycounter import FrequencyCounter


class ProbabilityTables:
    def __init__(self):
        # Declare Bayes Net parameter dicts
        # For feature value x and arrival status s,
        # Structure is p(x | s) = dict[x][s]
        # e.g. p(Monday|0-14min delay) = self.p_day['1']['delay:0']
        self.p_status: dict[str, float] = None
        self.p_day: dict[str, dict[str, float]] = None
        self.p_airline: dict[str, dict[str, float]] = None
        self.p_src: dict[str, dict[str, float]] = None
        self.p_dst: dict[str, dict[str, float]] = None
        self.p_dep_time: dict[str, dict[str, float]] = None
        self.p_src_tmp: dict[str, dict[str, float]] = None
        self.p_dst_tmp: dict[str, dict[str, float]] = None
        self.p_src_wnd: dict[str, dict[str, float]] = None
        self.p_dst_wnd: dict[str, dict[str, float]] = None

        self.__k: int = None

        # Flag indicating whether tables are initialized to values
        self.__p_tables_reset: bool = False
        self.__p_tables_fit: bool = False

    def reset_tables(self, key_meta: KeyMeta, frequencies: FrequencyCounter):
        """Initializes tables with new keys and zero values.
        Keys derived from arguments."""
        self.__p_tables_fit = False
        self.__p_tables_reset = True
        self.__k = None
        self.p_status = dict.fromkeys(
            key_meta.get_status_keys(), 0)

        self.p_day = {key: self.p_status.copy()
                      for key in frequencies.get_day_counter().keys()}

        self.p_airline = {key: self.p_status.copy()
                          for key in frequencies.get_airline_counter().keys()}

        self.p_src = {key: self.p_status.copy()
                      for key in frequencies.get_src_counter().keys()}

        self.p_dst = {key: self.p_status.copy()
                      for key in frequencies.get_dst_counter().keys()}

        self.p_dep_time = {key: self.p_status.copy()
                           for key in frequencies.get_dep_time_counter().keys()}

        self.p_src_tmp = {key: self.p_status.copy()
                          for key in frequencies.get_src_tmp_counter().keys()}

        self.p_dst_tmp = {key: self.p_status.copy()
                          for key in frequencies.get_dst_tmp_counter().keys()}

        self.p_src_wnd = {key: self.p_status.copy()
                          for key in frequencies.get_src_wind_counter().keys()}

        self.p_dst_wnd = {key: self.p_status.copy()
                          for key in frequencies.get_dst_wind_counter().keys()}

    def fit(self, dataset: Dataset, frequencies: FrequencyCounter, k: int):
        """Fits the tables to a dataset.

        Positional arguments:
        - dataset -- `Dataset` from which variable frequencies were drawn
        - frequencies -- `FrequencyCounter` on which `count_frequencies()`
                         has been invoked
        - k -- laplace smoothing coefficient to use
        """
        # Test and validation data were not used for frequency calculation
        # and should be omitted from data_len.
        data_len = dataset.get_training_len()
        if not self.__p_tables_reset:
            raise BufferError(
                'ProbabilityTables: ERR: Tables were not reset. Run reset_tables() first.')
        # Calculate p values
        for status_k in self.p_status.keys():
            status_freq = frequencies.query_status_counter(status_k)
            self.p_status[status_k] = self.__laplace_smooth(
                status_freq, data_len, len(self.p_status.keys()), k)
            for key in self.p_day.keys():
                self.p_day[key][status_k] = self.__laplace_smooth(
                    frequencies.query_day_counter(key, status_k), status_freq, len(self.p_day.keys()), k)

            for key in self.p_airline.keys():
                self.p_airline[key][status_k] = self.__laplace_smooth(
                    frequencies.query_airline_counter(key, status_k), status_freq, len(self.p_airline.keys()), k)

            for key in self.p_src.keys():
                self.p_src[key][status_k] = self.__laplace_smooth(
                    frequencies.query_src_counter(key, status_k), status_freq, len(self.p_src.keys()), k)

            for key in self.p_dst.keys():
                self.p_dst[key][status_k] = self.__laplace_smooth(
                    frequencies.query_dst_counter(key, status_k), status_freq, len(self.p_dst.keys()), k)

            for key in self.p_dep_time.keys():
                self.p_dep_time[key][status_k] = self.__laplace_smooth(
                    frequencies.query_dep_time_counter(key, status_k), status_freq, len(self.p_dep_time.keys()), k)

            for key in self.p_src_tmp.keys():
                self.p_src_tmp[key][status_k] = self.__laplace_smooth(
                    frequencies.query_src_tmp_counter(key, status_k), status_freq, len(self.p_src_tmp.keys()), k)

            for key in self.p_dst_tmp.keys():
                self.p_dst_tmp[key][status_k] = self.__laplace_smooth(
                    frequencies.query_dst_tmp_counter(key, status_k), status_freq, len(self.p_dst_tmp.keys()), k)

            for key in self.p_src_wnd.keys():
                self.p_src_wnd[key][status_k] = self.__laplace_smooth(
                    frequencies.query_src_wnd_counter(key, status_k), status_freq, len(self.p_src_wnd.keys()), k)

            for key in self.p_dst_wnd.keys():
                self.p_dst_wnd[key][status_k] = self.__laplace_smooth(
                    frequencies.query_dst_wnd_counter(key, status_k), status_freq, len(self.p_dst_wnd.keys()), k)

        self.__k = k
        self.__p_tables_fit = True
        self.__p_tables_reset = False

    def get_k(self):
        """Get the smoothing coefficient used for the last call to `fit()`."""
        return self.__k

    def is_fit(self):
        """Test whether the tables have been fit to data."""
        return self.__p_tables_fit

    def import_p_tables(self, tables: dict):
        """Import p tables from a dictionary.

        Input:

        dict with the following keys:
        - 'arrival_status'
        - 'day'
        - 'airline'
        - 'src_airport'
        - 'dst_airport'
        - 'departure_time'
        - 'src_temperature'
        - 'dst_temperature'
        - 'src_wind_speed'
        - 'dst_wind_speed'

        Each value in the dict is a properly formatted p_table.
        """
        self.p_status = deepcopy(tables['arrival_status'])
        self.p_day = deepcopy(tables['day'])
        self.p_airline = deepcopy(tables['airline'])
        self.p_src = deepcopy(tables['src_airport'])
        self.p_dst = deepcopy(tables['dst_airport'])
        self.p_dep_time = deepcopy(tables['departure_time'])
        self.p_src_tmp = deepcopy(tables['src_temperature'])
        self.p_dst_tmp = deepcopy(tables['dst_temperature'])
        self.p_src_wnd = deepcopy(tables['src_wind_speed'])
        self.p_dst_wnd = deepcopy(tables['dst_wind_speed'])
        self.__p_tables_fit = True
        self.__p_tables_reset = False

    def export_p_tables(self) -> dict[str, dict]:
        """Dumps p tables to a JSON-friendly dict and returns it.

        Returns:

        dict with keys:
        - 'arrival_status'
        - 'day'
        - 'airline'
        - 'src_airport'
        - 'dst_airport'
        - 'departure_time'
        - 'src_temperature'
        - 'dst_temperature'
        - 'src_wind_speed'
        - 'dst_wind_speed'
        """
        return {
            'arrival_status': self.p_status,
            'day': self.p_day,
            'airline': self.p_airline,
            'src_airport': self.p_src,
            'dst_airport': self.p_dst,
            'departure_time': self.p_dep_time,
            'src_temperature': self.p_src_tmp,
            'dst_temperature': self.p_dst_tmp,
            'src_wind_speed': self.p_src_wnd,
            'dst_wind_speed': self.p_dst_wnd
        }

    # QUERY FUNCTIONS
    # Given a key and an arrival status, these functions return
    # P(variable = key | arrival status)

    def query_p_status(self, status: str) -> float:
        return self.p_status[status]

    def query_p_day(self, day: str, status: str) -> float:
        return self.p_day[day][status]

    def query_p_airline(self, airline: str, status: str) -> float:
        return self.p_airline[airline][status]

    def query_p_src(self, src: str, status: str) -> float:
        return self.p_src[src][status]

    def query_p_dst(self, dst: str, status: str) -> float:
        return self.p_dst[dst][status]

    def query_p_dep_time(self, dep_time: str, status: str) -> float:
        return self.p_dep_time[dep_time][status]

    def query_p_src_tmp(self, src_tmp: str, status: str) -> float:
        return self.p_src_tmp[src_tmp][status]

    def query_p_dst_tmp(self, dst_tmp: str, status: str) -> float:
        return self.p_dst_tmp[dst_tmp][status]

    def query_p_src_wnd(self, src_wnd: str, status: str) -> float:
        return self.p_src_wnd[src_wnd][status]

    def query_p_dst_wnd(self, dst_wnd: str, status: str) -> float:
        return self.p_dst_wnd[dst_wnd][status]

    # GETTERS
    # All getters use either copy() or deepcopy(). For better performance,
    # consider a query function instead.

    def get_p_status(self) -> dict[str, float]:
        return self.p_status.copy()

    def get_p_day(self) -> dict[str, dict[str, float]]:
        return deepcopy(self.p_day)

    def get_p_airline(self) -> dict[str, dict[str, float]]:
        return deepcopy(self.p_airline)

    def get_p_src(self) -> dict[str, dict[str, float]]:
        return deepcopy(self.p_src)

    def get_p_dst(self) -> dict[str, dict[str, float]]:
        return deepcopy(self.p_dst)

    def get_p_dep_time(self) -> dict[str, dict[str, float]]:
        return deepcopy(self.p_dep_time)

    def get_p_src_tmp(self) -> dict[str, dict[str, float]]:
        return deepcopy(self.p_src_tmp)

    def get_p_dst_tmp(self) -> dict[str, dict[str, float]]:
        return deepcopy(self.p_dst_tmp)

    def get_p_src_wnd(self) -> dict[str, dict[str, float]]:
        return deepcopy(self.p_src_wnd)

    def get_p_dst_wnd(self) -> dict[str, dict[str, float]]:
        return deepcopy(self.p_dst_wnd)

    def __laplace_smooth(self, observations_freq: int, total: int, dimension: int, k: int):
        """Calculate the probability that a random variable takes a value.

        Positional arguments:

        - observations_freq -- frequency of the value of a random variable for
                             which probability is calculated
        - total -- frequency of all values of the random variable
        - dimension -- number of values the random variable can take
        - k -- laplace smoothing coefficient to apply

        Returns:

        Smoothed probability that the variable takes the relevant value
        """
        if total == 0 and (dimension == 0 or k == 0):
            return 0  # Avoid DivideByZero exception

        return (observations_freq + k) / (total + dimension * k)
