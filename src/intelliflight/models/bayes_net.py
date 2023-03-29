from . import ai_model
import random
import math
import csv
import datetime
import json

from ..util import datautil


class Bayes_Net(ai_model.AI_Model):
    def __init__(self, params_path: str = None):
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
        self.p_dst_wind: dict[str, dict[str, float]] = None
        # Flag indicating whether tables are initialized to values
        self.p_tables_set: bool = False

        # Frequency dicts. These store the frequency of variables
        # in the training data and are used to generate probability values.
        self.status_counter: dict[str, int] = None
        self.day_counter: dict[str, dict[str, int]] = None
        self.airline_counter: dict[str, dict[str, int]] = None
        self.src_counter: dict[str, dict[str, int]] = None
        self.dst_counter: dict[str, dict[str, int]] = None
        self.dep_time_counter: dict[str, dict[str, int]] = None
        self.src_tmp_counter: dict[str, dict[str, int]] = None
        self.dst_tmp_counter: dict[str, dict[str, int]] = None
        self.src_wind_counter: dict[str, dict[str, int]] = None
        self.dst_wind_counter: dict[str, dict[str, int]] = None

        # Information about which features occur in the training data
        self.seen_airports: set = None
        self.seen_carriers: set = None

        # Parameters used to train model
        self.rng_seed: int = None

        super().__init__(params_path)

        # Generate key values for possible arrival states:
        # -Arrived at destination (ahead, on-time, or delayed) [delay:<code>]
        # -Cancelled [cancel:<code>]
        # -Diverted to another airport [divert]
        self.ARRIVAL_STATUSES: dict[str, str] = {}
        # Open files containing codes and descriptions for arrival delay/ahead/on-time buckets
        # and cancellation reasons.
        with open('data/maps/L_CANCELLATION.csv', 'r', encoding='utf-8') as cancel_in, \
                open('data/maps/L_ONTIME_DELAY_GROUPS.csv', 'r', encoding='utf-8') as delay_in:
            cancellation_codes = csv.DictReader(cancel_in)
            delay_groups = csv.DictReader(delay_in)

            # Format:
            # { 'cancel:<code>': <associated cancellation reason> }
            for code in cancellation_codes:
                self.ARRIVAL_STATUSES[f'cancel:{code["Code"]}'] = code['Description']

            # Format:
            # { 'delay:<code>': <description of time range for bucket> }
            for delay in delay_groups:
                self.ARRIVAL_STATUSES[f'delay:{delay["Code"]}'] = delay['Description']

            # Format:
            # { 'divert': 'Diverted' }
            self.ARRIVAL_STATUSES['divert'] = 'Diverted'

            # Generate values for departure time buckets. Format:
            # [ '0000', '0030', '0100', ..., '2300', '2330' ]
            self.DEP_TIMES: list[str] = []
            for i in range(24):
                for j in ['00', '30']:
                    self.DEP_TIMES.append(f'{str(i).rjust(2, "0")}{j}')

            # Pull keys for temperature and wind buckets
            with open('data/maps/temp_ranges.csv', 'r', encoding='utf-8') as temp_in, \
                    open('data/maps/wind_speeds.csv', 'r', encoding='utf-8') as wind_in:
                temp_codes = csv.DictReader(temp_in)
                wind_codes = csv.DictReader(wind_in)
                self.TEMP_KEYS: list[str] = [code['key']
                                             for code in temp_codes]
                self.WIND_KEYS: list[str] = [code['key']
                                             for code in wind_codes]

    def load_params(self, path: str):
        """"""
        with open(path, 'r') as f_in:
            import_json = json.load(f_in)
            # Load training RNG seed
            rng_seed = import_json['training_rng_seed']

            # Load seen airports and airlines
            seen_airports = set(import_json['seen_airports'])
            seen_carriers = set(import_json['seen_carriers'])

            # Load probability tables
            p_status = import_json['p_tables']['arrival_status']
            p_day = import_json['p_tables']['day']
            p_airline = import_json['p_tables']['airline']
            p_src = import_json['p_tables']['src_airport']
            p_dst = import_json['p_tables']['dst_airport']
            p_dep_time = import_json['p_tables']['departure_time']
            p_src_tmp = import_json['p_tables']['src_temperature']
            p_dst_tmp = import_json['p_tables']['dst_temperature']
            p_src_wnd = import_json['p_tables']['src_wind_speed']
            p_dst_wind = import_json['p_tables']['dst_wind_speed']

            # If all loading succeeded, update member variables
            self.rng_seed = rng_seed
            self.seen_airports = seen_airports
            self.seen_carriers = seen_carriers
            self.set_p_tables(p_status, p_day, p_airline, p_src, p_dst,
                              p_dep_time, p_src_tmp, p_dst_tmp, p_src_wnd, p_dst_wind)

    def train_model(self, flight_path: str, partition_count: int, k_step_percent: float, max_k_fraction: float, rng_seed: int = None):
        start_t: datetime.datetime = datetime.datetime.now().timestamp()
        if rng_seed is None:
            rng_seed = int(random.random() * 1000000000)
        self.rng_seed = rng_seed
        print(f'BayesNet: RNG seed is {self.rng_seed}.')

        # Process dataset
        print('BayesNet: Merging training datasets.')
        data, self.seen_carriers, seen_src, seen_dst = datautil.merge_training_data(
            flight_path, 'data/historical/weather/weather_by_bts_id.json')
        self.seen_airports = seen_src.copy()
        for dst in seen_dst:
            self.seen_airports.add(dst)
        print('BayesNet: Discretizing data.')
        datautil.discretize(data)
        print('BayesNet: Shuffling and partitioning data.')
        partitions = datautil.shuffle_and_partition(
            data, self.rng_seed, partition_count)

        # Determine laplace smoothing hyperparameter (k) using k-fold cross-validation with validation and test set
        data_len = len(data)
        max_k = math.floor(data_len * max_k_fraction)
        k_step = math.floor(data_len * k_step_percent)
        k_values = list(range(0, max_k, k_step))
        k_test_results = []

        for test_index in range(len(partitions)):
            print(
                f'BayesNet: Processing test partition {test_index + 1} of {len(partitions)}.')
            test_start = partitions[test_index]
            test_end = None  # Index of first item AFTER test set
            if test_start == partitions[-1]:
                test_end = data_len
            else:
                test_end = partitions[test_index + 1]

            k_validation_results = {k: 0 for k in k_values}

            passed_test_partition = False  # for logging
            for validation_index in range(len(partitions)):
                validation_start = partitions[validation_index]
                validation_end = None
                if validation_index == test_index:
                    passed_test_partition = True
                    continue
                elif validation_start == partitions[-1]:
                    validation_end = data_len
                else:
                    validation_end = partitions[validation_index + 1]

                validation_pass = \
                    validation_index + 1 - int(passed_test_partition)
                print(
                    f'BayesNet:   Processing validation partition {validation_pass} of {len(partitions) - 1}.')

                self.count_frequencies(
                    data, data_len, test_start, test_end, validation_start, validation_end)

                for k in k_values:
                    print(
                        f'BayesNet:     Fitting model with k={k}.')
                    self.fit_p(data_len, k)

                    print(
                        f'BayesNet:     Testing model with k={k}.')
                    error = self.test(data, validation_start, validation_end)
                    accuracy = round((1 - error) * 100, 2)
                    print(
                        f'BayesNet:     Accuracy was {accuracy}%.')
                    # Incrementally adjust average
                    k_validation_results[k] += (error -
                                                k_validation_results[k]) / validation_pass

            # TODO: Pick best performing k
            best_k = None
            best_error = 2
            for k, avg_error in k_validation_results.items():
                if avg_error < best_error:
                    best_k = k
                    best_error = avg_error

            print(
                f'BayesNet:   Refitting model with best k value from cross-validation (k={best_k}).')
            # Using best k, refit to all data except test set
            self.count_frequencies(data, data_len, test_start, test_end)
            self.fit_p(data_len, best_k)
            print(
                f'BayesNet:   Testing refit model.')
            error = self.test(data, test_start, test_end)
            accuracy = round((1 - error) * 100, 2)
            print(
                f'BayesNet:   Accuracy was {accuracy}%.')
            k_test_results.append({'k': best_k, 'error': error})

        # Pick k value that performed best on test set
        best_k = None
        best_error = 2
        for iteration in k_test_results:
            if iteration['error'] < best_error:
                best_k = iteration['k']
                best_error = iteration['error']

        print(
            f'BayesNet: Refitting model with best k value from testing (k={best_k}).')
        # Fit to all data with best k
        self.count_frequencies(data, data_len)
        self.fit_p(data_len, best_k)
        # self.export_parameters()
        accuracy = round((1 - best_error) * 100, 2)
        print(
            f'BayesNet: Best model has k={best_k} and an estimated accuracy of {accuracy}%.')
        print(
            f'BayesNet: Completed training in {round(datetime.datetime.now().timestamp() - start_t, 2)}s.')

    def laplace_smooth(self, observations_freq: int, total: int, dimension: int, k: int):
        if total == 0 and (dimension == 0 or k == 0):
            return 0  # Avoid DivideByZero exception

        return (observations_freq + k) / (total + dimension * k)

    def fit_p(self, data_len: int, k: int):
        # Initialize probability dicts
        p_status = dict.fromkeys(self.ARRIVAL_STATUSES.keys(), 0)

        p_day = {key: p_status.copy()
                 for key in self.day_counter.keys()}

        p_airline = {key: p_status.copy()
                     for key in self.airline_counter.keys()}

        p_src = {key: p_status.copy()
                 for key in self.src_counter.keys()}

        p_dst = {key: p_status.copy()
                 for key in self.dst_counter.keys()}

        p_dep_time = {key: p_status.copy()
                      for key in self.dep_time_counter.keys()}

        p_src_tmp = {key: p_status.copy()
                     for key in self.src_tmp_counter.keys()}

        p_dst_tmp = {key: p_status.copy()
                     for key in self.dst_tmp_counter.keys()}

        p_src_wnd = {key: p_status.copy()
                     for key in self.src_wind_counter.keys()}

        p_dst_wnd = {key: p_status.copy()
                     for key in self.dst_wind_counter.keys()}

        # Calculate p values
        for status_k in p_status.keys():
            p_status[status_k] = self.laplace_smooth(
                self.status_counter[status_k], data_len, len(p_status.keys()), k)
            for key in p_day.keys():
                p_day[key][status_k] = self.laplace_smooth(
                    self.day_counter[key][status_k], self.status_counter[status_k], len(p_day.keys()), k)

            for key in p_airline.keys():
                p_airline[key][status_k] = self.laplace_smooth(
                    self.airline_counter[key][status_k], self.status_counter[status_k], len(p_airline.keys()), k)

            for key in p_src.keys():
                p_src[key][status_k] = self.laplace_smooth(
                    self.src_counter[key][status_k], self.status_counter[status_k], len(p_src.keys()), k)

            for key in p_dst.keys():
                p_dst[key][status_k] = self.laplace_smooth(
                    self.dst_counter[key][status_k], self.status_counter[status_k], len(p_dst.keys()), k)

            for key in p_dep_time.keys():
                p_dep_time[key][status_k] = self.laplace_smooth(
                    self.dep_time_counter[key][status_k], self.status_counter[status_k], len(p_dep_time.keys()), k)

            for key in p_src_tmp.keys():
                p_src_tmp[key][status_k] = self.laplace_smooth(
                    self.src_tmp_counter[key][status_k], self.status_counter[status_k], len(p_src_tmp.keys()), k)

            for key in p_dst_tmp.keys():
                p_dst_tmp[key][status_k] = self.laplace_smooth(
                    self.dst_tmp_counter[key][status_k], self.status_counter[status_k], len(p_dst_tmp.keys()), k)

            for key in p_src_wnd.keys():
                p_src_wnd[key][status_k] = self.laplace_smooth(
                    self.src_wind_counter[key][status_k], self.status_counter[status_k], len(p_src_wnd.keys()), k)

            for key in p_dst_wnd.keys():
                p_dst_wnd[key][status_k] = self.laplace_smooth(
                    self.dst_wind_counter[key][status_k], self.status_counter[status_k], len(p_dst_wnd.keys()), k)

        # Update instance p dicts
        self.set_p_tables(p_status, p_day, p_airline, p_src, p_dst,
                          p_dep_time, p_src_tmp, p_dst_tmp, p_src_wnd, p_dst_wnd)

    def export_parameters(self):
        export_json = {}
        export_json['training_rng_seed'] = self.rng_seed
        export_json['seen_airports'] = list(self.seen_airports)
        export_json['seen_carriers'] = list(self.seen_carriers)
        export_json['p_tables'] = {
            'arrival_status': self.p_status,
            'day': self.p_day,
            'airline': self.p_airline,
            'src_airport': self.p_src,
            'dst_airport': self.p_dst,
            'departure_time': self.p_dep_time,
            'src_temperature': self.p_src_tmp,
            'dst_temperature': self.p_dst_tmp,
            'src_wind_speed': self.p_src_wnd,
            'dst_wind_speed': self.p_dst_wind
        }
        with open('data/models/bayes_net.model.json', 'w') as f_out:
            json.dump(export_json, f_out)

    def count_frequencies(self, dataset: list, data_len: int, test_start: int = None, test_end: int = None, validation_start: int = None, validation_end: int = None):
        # Reset frequency counters
        self.status_counter = {
            key: 0 for key in self.ARRIVAL_STATUSES.keys()}

        self.day_counter = {str(day_k): self.status_counter.copy()
                            for day_k in range(1, 8)}

        self.airline_counter = {aline_k: self.status_counter.copy()
                                for aline_k in self.seen_carriers}

        self.src_counter = {src_k: self.status_counter.copy()
                            for src_k in self.seen_airports}

        self.dst_counter = self.src_counter.copy()

        self.dep_time_counter = {dep_k: self.status_counter.copy()
                                 for dep_k in self.DEP_TIMES}

        self.src_tmp_counter = {tmp_k: self.status_counter.copy()
                                for tmp_k in self.TEMP_KEYS}

        self.dst_tmp_counter = self.src_tmp_counter.copy()

        self.src_wind_counter = {wnd_k: self.status_counter.copy()
                                 for wnd_k in self.WIND_KEYS}

        self.dst_wind_counter = self.src_wind_counter.copy()

        # Error checking

        # Validation bounds must both be None or both have values
        if (validation_start is None) != (validation_end is None):
            raise TypeError(
                f'BayesNet.count_frequencies(): Provided validation_start={validation_start} and validation_end={validation_end} (Either both or neither must be None).')
        elif validation_start is None:
            # Test bounds must both be None or both have values
            if (test_start is None) != (test_end is None):
                raise TypeError(
                    f'BayesNet.count_frequencies(): Provided test_start={test_start} and test_end={test_end} (Either both or neither must be None).')
            # If there is no test set, make the bounds negative so the index in the dataset never falls between them
            if test_start is None:
                test_start = -999
                test_end = -999
            # test_end must come after test_start
            elif test_start > test_end:
                raise ValueError(
                    f'BayesNet.count_frequencies(): test_start={test_start} > test_end={test_end}')
            # Set bounds to test set bounds
            validation_start = test_start
            validation_end = test_end
        else:
            # Cannot have validation set but no test set
            if test_start is None or test_end is None:
                raise TypeError(
                    'BayesNet.count_frequencies(): Test set boundaries cannot be None if a validation set is defined.')
            # test_end must come after test_start
            if test_start > test_end:
                raise ValueError(
                    f'BayesNet.count_frequencies(): test_start={test_start} > test_end={test_end}')
            # validation_end must come after validation_start
            if validation_start > validation_end:
                raise ValueError(
                    f'BayesNet.count_frequencies(): validation_start={validation_start} > validation_end={validation_end}')

        # Determine which records are not in test or validation sets
        training_range = [i for i in range(data_len) if not (
            (test_start <= i < test_end) or (validation_start <= i < validation_end))]

        # Count variables
        for i in training_range:
            record = dataset[i]
            # Process arrival status
            status_k = None
            if record['CANCELLED'] == '1.00':
                status_k = f'cancel:{record["CANCELLATION_CODE"]}'
            elif record['DIVERTED'] == '1.00':
                status_k = 'divert'
            else:
                status_k = f'delay:{record["ARR_DELAY_GROUP"]}'

            self.status_counter[status_k] += 1

            # Process other variables
            self.day_counter[record['DAY_OF_WEEK']][status_k] += 1
            self.airline_counter[record['OP_UNIQUE_CARRIER']
                                 ][status_k] += 1
            self.src_counter[record['ORIGIN_AIRPORT_ID']
                             ][status_k] += 1
            self.dst_counter[record['DEST_AIRPORT_ID']][status_k] += 1
            self.dep_time_counter[record['CRS_DEP_TIME']
                                  ][status_k] += 1
            self.src_tmp_counter[record['src_tavg']][status_k] += 1
            self.dst_tmp_counter[record['dst_tavg']][status_k] += 1
            self.src_wind_counter[record['src_wspd']][status_k] += 1
            self.dst_wind_counter[record['dst_wspd']][status_k] += 1

    def set_p_tables(self, p_status, p_day, p_airline, p_src, p_dst, p_dep_time, p_src_tmp, p_dst_tmp, p_src_wnd, p_dst_wnd):
        """"""
        self.p_status = p_status
        self.p_day = p_day
        self.p_airline = p_airline
        self.p_src = p_src
        self.p_dst = p_dst
        self.p_dep_time = p_dep_time
        self.p_src_tmp = p_src_tmp
        self.p_dst_tmp = p_dst_tmp
        self.p_src_wnd = p_src_wnd
        self.p_dst_wind = p_dst_wnd
        self.p_tables_set = True

    def test(self, dataset: list, test_start: int, test_end: int):
        num_pass = 0
        num_fail = 0
        for i in range(test_start, test_end):
            record = dataset[i]
            predicted_status, _ = self.make_prediction(record['ORIGIN_AIRPORT_ID'], record['DEST_AIRPORT_ID'], record['OP_UNIQUE_CARRIER'],
                                                       record['DAY_OF_WEEK'], record['CRS_DEP_TIME'], record['src_tavg'], record['dst_tavg'], record['src_wspd'], record['dst_wspd'])
            if predicted_status == 'divert' and record['DIVERTED'] == '1.00':
                print('divert')
                num_pass += 1
            elif 'delay:' in predicted_status and record['ARR_DELAY_GROUP'] == predicted_status.split(':')[1]:
                num_pass += 1
            elif 'cancel:' in predicted_status and record['CANCELLATION_CODE'] == predicted_status.split(':')[1]:
                num_pass += 1
            else:
                num_fail += 1

        return num_fail / (num_pass + num_fail)

    def make_prediction(self, src_airport: int, dest_airport: int, operating_airline: str, day_of_week: int, departure_time: str, src_tmp: str, dst_tmp: str, src_wnd: str, dst_wnd: str):
        if src_airport not in self.seen_airports:
            raise ValueError(
                f'BayesNet: src_airport={src_airport} did not occur in the training data.')
        if dest_airport not in self.seen_airports:
            raise ValueError(
                f'BayesNet: dest_airport={dest_airport} did not occur in the training data.')
        if operating_airline not in self.seen_carriers:
            raise ValueError(
                f'BayesNet: operating_airline={operating_airline} did not occur in the training data.')

        src_airport = str(src_airport)
        dest_airport = str(dest_airport)
        day_of_week = str(day_of_week)

        predicted_p = dict.fromkeys(self.p_status.keys())
        for key in predicted_p.keys():
            factors = [
                self.p_status[key],
                self.p_airline[operating_airline][key],
                self.p_day[day_of_week][key],
                self.p_dep_time[departure_time][key],
                self.p_src[src_airport][key],
                self.p_dst[dest_airport][key],
                self.p_src_tmp[src_tmp][key],
                self.p_dst_tmp[dst_tmp][key],
                self.p_src_wnd[src_wnd][key],
                self.p_dst_wind[dst_wnd][key]
            ]
            predicted_p[key] = math.prod(factors)

        sum_intermediates = sum(predicted_p.values())
        best_key = None
        best_p = -1
        for k, p in predicted_p.items():
            predicted_p[k] = p / sum_intermediates
            if predicted_p[k] > best_p:
                best_key = k
                best_p = predicted_p[k]

        return best_key, best_p
