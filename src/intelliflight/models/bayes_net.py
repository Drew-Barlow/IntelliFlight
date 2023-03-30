from . import ai_model
import random
import math
import csv
import datetime
import json

from ..util import datautil
from intelliflight.models.components.dataset import Dataset
from intelliflight.models.components.keymeta import KeyMeta
from intelliflight.models.components.frequencycounter import FrequencyCounter
from intelliflight.models.components.ptables import ProbabilityTables


class Bayes_Net(ai_model.AI_Model):
    def __init__(self, params_path: str = None):
        # Declare model components
        self.key_meta = KeyMeta()
        self.dataset = Dataset()
        self.frequencies = FrequencyCounter()
        self.p_tables = ProbabilityTables()

        # Parameters used to train model
        self.rng_seed: int = None

        super().__init__(params_path)

        # Generate key values for possible arrival states:
        # -Arrived at destination (ahead, on-time, or delayed) [delay:<code>]
        # -Cancelled [cancel:<code>]
        # -Diverted to another airport [divert]
        arrival_statuses: dict[str, str] = {}
        # Open files containing codes and descriptions for arrival delay/ahead/on-time buckets
        # and cancellation reasons.
        with open('data/maps/L_CANCELLATION.csv', 'r', encoding='utf-8') as cancel_in, \
                open('data/maps/L_ONTIME_DELAY_GROUPS.csv', 'r', encoding='utf-8') as delay_in:
            cancellation_codes = csv.DictReader(cancel_in)
            delay_groups = csv.DictReader(delay_in)

            # Format:
            # { 'cancel:<code>': <associated cancellation reason> }
            for code in cancellation_codes:
                arrival_statuses[f'cancel:{code["Code"]}'] = code['Description']

            # Format:
            # { 'delay:<code>': <description of time range for bucket> }
            for delay in delay_groups:
                arrival_statuses[f'delay:{delay["Code"]}'] = delay['Description']

            # Format:
            # { 'divert': 'Diverted' }
            arrival_statuses['divert'] = 'Diverted'

            self.key_meta.set_arrival_statuses(arrival_statuses)

            # Pull keys for temperature and wind buckets
            with open('data/maps/temp_ranges.csv', 'r', encoding='utf-8') as temp_in, \
                    open('data/maps/wind_speeds.csv', 'r', encoding='utf-8') as wind_in:
                temp_codes = csv.DictReader(temp_in)
                wind_codes = csv.DictReader(wind_in)
                self.key_meta.set_temp_keys(
                    [code['key'] for code in temp_codes])
                self.key_meta.set_wind_keys(
                    [code['key'] for code in wind_codes])

    def load_params(self, path: str):
        """"""
        with open(path, 'r') as f_in:
            import_json = json.load(f_in)
            # Load training RNG seed
            rng_seed = import_json['training_rng_seed']

            # Load seen airports and airlines
            seen_airports = set(import_json['seen_airports'])
            seen_carriers = set(import_json['seen_carriers'])

            self.p_tables.import_p_tables(import_json['p_tables'])

            # If all loading succeeded, update member variables
            self.rng_seed = rng_seed
            self.key_meta.set_seen_airports(seen_airports)
            self.key_meta.set_seen_carriers(seen_carriers)

    def load_data(self, flight_path: str):
        print('BayesNet: Merging training datasets.')
        data, seen_carriers, seen_src, seen_dst = datautil.merge_training_data(
            flight_path, 'data/historical/weather/weather_by_bts_id.json')
        seen_airports = seen_src.copy()
        for dst in seen_dst:
            seen_airports.add(dst)
        self.key_meta.set_seen_airports(seen_airports)
        self.key_meta.set_seen_carriers(seen_carriers)
        print('BayesNet: Discretizing data.')
        datautil.discretize(data)
        self.dataset.set_data(data)

    def train_model(self, partition_count: int, k_step_percent: float, max_k_fraction: float, rng_seed: int = None):
        if self.dataset.get_data() is None:
            raise BufferError(
                'BayesNet: ERR: No data loaded. Call load_data() first.')
        start_t: datetime.datetime = datetime.datetime.now().timestamp()
        if rng_seed is None:
            rng_seed = int(random.random() * 1000000000)
        self.rng_seed = rng_seed
        print(f'BayesNet: RNG seed is {self.rng_seed}.')

        print('BayesNet: Shuffling and partitioning data.')
        partitions = datautil.shuffle_and_partition(
            self.dataset.get_data(), self.rng_seed, partition_count)

        # Determine laplace smoothing hyperparameter (k) using k-fold cross-validation with validation and test set
        data_len = self.dataset.get_len()
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

            self.dataset.set_test_bounds(test_start, test_end)

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

                self.dataset.set_validation_bounds(
                    validation_start, validation_end)

                validation_pass = \
                    validation_index + 1 - int(passed_test_partition)
                print(
                    f'BayesNet:   Processing validation partition {validation_pass} of {len(partitions) - 1}.')

                self.frequencies.reset_counters(self.key_meta)
                self.frequencies.count_frequencies(self.dataset)

                for k in k_values:
                    print(
                        f'BayesNet:     Fitting model with k={k}.')
                    self.p_tables.reset_tables(self.key_meta, self.frequencies)
                    self.p_tables.fit(self.dataset, self.frequencies, k)

                    print(
                        f'BayesNet:     Testing model with k={k}.')
                    error = self.test(self.dataset.get_validation_bounds())
                    accuracy = round((1 - error) * 100, 2)
                    print(
                        f'BayesNet:     Accuracy was {accuracy}%.')
                    # Incrementally adjust average
                    k_validation_results[k] += (error -
                                                k_validation_results[k]) / validation_pass

            best_k = None
            best_error = 2
            for k, avg_error in k_validation_results.items():
                if avg_error < best_error:
                    best_k = k
                    best_error = avg_error

            print(
                f'BayesNet:   Refitting model with best k value from cross-validation (k={best_k}).')
            self.dataset.clear_validation_partition()
            # Using best k, refit to all data except test set
            self.frequencies.reset_counters(self.key_meta)
            self.frequencies.count_frequencies(self.dataset)
            self.p_tables.reset_tables(self.key_meta, self.frequencies)
            self.p_tables.fit(self.dataset, self.frequencies, best_k)
            print(
                f'BayesNet:   Testing refit model.')
            error = self.test(self.dataset.get_test_bounds())
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
        self.dataset.clear_test_partition()
        # Fit to all data with best k
        self.frequencies.reset_counters(self.key_meta)
        self.frequencies.count_frequencies(self.dataset)
        self.p_tables.reset_tables(self.key_meta, self.frequencies)
        self.p_tables.fit(self.dataset, self.frequencies, best_k)
        accuracy = round((1 - best_error) * 100, 2)
        print(
            f'BayesNet: Best model has k={best_k} and an estimated accuracy of {accuracy}%.')
        print(
            f'BayesNet: Completed training in {round(datetime.datetime.now().timestamp() - start_t, 2)}s.')

    def export_parameters(self):
        export_json = {}
        export_json['training_rng_seed'] = self.rng_seed
        export_json['seen_airports'] = list(self.key_meta.get_seen_airports())
        export_json['seen_carriers'] = list(self.key_meta.get_seen_carriers())
        export_json['p_tables'] = self.p_tables.export_p_tables()
        with open('data/models/bayes_net.model.json', 'w') as f_out:
            json.dump(export_json, f_out)

    def test(self, test_bounds: tuple[int, int]):
        num_pass = 0
        num_fail = 0
        test_start, test_end = test_bounds
        data = self.dataset.get_data()
        for i in range(test_start, test_end):
            record = data[i]
            predicted_status, _ = self.make_prediction(record['ORIGIN_AIRPORT_ID'], record['DEST_AIRPORT_ID'], record['OP_UNIQUE_CARRIER'],
                                                       record['DAY_OF_WEEK'], record['CRS_DEP_TIME'], record['src_tavg'], record['dst_tavg'], record['src_wspd'], record['dst_wspd'])
            if predicted_status == 'divert' and record['DIVERTED'] == '1.00':
                num_pass += 1
            elif 'delay:' in predicted_status and record['ARR_DELAY_GROUP'] == predicted_status.split(':')[1]:
                num_pass += 1
            elif 'cancel:' in predicted_status and record['CANCELLATION_CODE'] == predicted_status.split(':')[1]:
                num_pass += 1
            else:
                num_fail += 1

        return num_fail / (num_pass + num_fail)

    def make_prediction(self, src_airport: int, dest_airport: int, operating_airline: str, day_of_week: int, departure_time: str, src_tmp: str, dst_tmp: str, src_wnd: str, dst_wnd: str):
        if not self.key_meta.in_seen_airports(src_airport):
            raise ValueError(
                f'BayesNet: src_airport={src_airport} did not occur in the training data.')
        if not self.key_meta.in_seen_airports(dest_airport):
            raise ValueError(
                f'BayesNet: dest_airport={dest_airport} did not occur in the training data.')
        if not self.key_meta.in_seen_carriers(operating_airline):
            raise ValueError(
                f'BayesNet: operating_airline={operating_airline} did not occur in the training data.')

        src_airport = str(src_airport)
        dest_airport = str(dest_airport)
        day_of_week = str(day_of_week)

        predicted_p = dict.fromkeys(self.key_meta.get_status_keys())
        for key in predicted_p.keys():
            factors = [
                self.p_tables.query_p_status(key),
                self.p_tables.query_p_airline(operating_airline, key),
                self.p_tables.query_p_day(day_of_week, key),
                self.p_tables.query_p_dep_time(departure_time, key),
                self.p_tables.query_p_src(src_airport, key),
                self.p_tables.query_p_dst(dest_airport, key),
                self.p_tables.query_p_src_tmp(src_tmp, key),
                self.p_tables.query_p_dst_tmp(dst_tmp, key),
                self.p_tables.query_p_src_wnd(src_wnd, key),
                self.p_tables.query_p_dst_wnd(dst_wnd, key)
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
