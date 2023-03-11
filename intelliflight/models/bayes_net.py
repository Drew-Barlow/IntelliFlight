from . import ai_model
import random
import math
import csv

from ..util import datautil


class Bayes_Net(ai_model.AI_Model):
    def __init__(self, params_path=None):
        super().__init__(params_path)
        self.ARRIVAL_STATUSES = {}
        with open('data/maps/L_CANCELLATION.csv', 'r', encoding='utf-8') as cancel_in, \
                open('data/maps/L_ONTIME_DELAY_GROUPS.csv', 'r', encoding='utf-8') as delay_in:
            cancellation_codes = csv.DictReader(cancel_in)
            delay_groups = csv.DictReader(delay_in)
            for code in cancellation_codes:
                self.ARRIVAL_STATUSES[f'cancel:{code["Code"]}'] = code['Description']
            for delay in delay_groups:
                self.ARRIVAL_STATUSES[f'delay:{delay["Code"]}'] = delay['Description']
            self.ARRIVAL_STATUSES['divert'] = 'Diverted'

            self.DEP_TIMES = []
            for i in range(24):
                for j in ['00', '30']:
                    self.DEP_TIMES.append(f'{str(i).rjust(2, "0")}{j}')

            with open('data/maps/temp_ranges.csv', 'r', encoding='utf-8') as temp_in, \
                    open('data/maps/wind_speeds.csv', 'r', encoding='utf-8') as wind_in:
                temp_codes = csv.DictReader(temp_in)
                wind_codes = csv.DictReader(wind_in)
                self.TEMP_KEYS = [code['key'] for code in temp_codes]
                self.WIND_KEYS = [code['key'] for code in wind_codes]

    def load_params(self, path: str):
        raise NotImplementedError

    def train_model(self, flight_path: str, partition_count: int, k_step_percent: float, max_k_fraction: float, rng_seed: int = None):
        if rng_seed is None:
            rng_seed = int(random.random() * 1000000000)

        # Process dataset
        print('BayesNet: Merging training datasets.')
        data, seen_carriers, seen_src, seen_dst = datautil.merge_training_data(
            flight_path, 'data/historical/weather/weather_by_bts_id.json')
        seen_airports = seen_src.copy()
        for dst in seen_dst:
            seen_airports.add(dst)
        print('BayesNet: Discretizing data.')
        datautil.discretize(data)
        print('BayesNet: Shuffling and partitioning data.')
        partitions = datautil.shuffle_and_partition(
            data, rng_seed, partition_count)

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
                print(
                    f'BayesNet:     Processing validation partition {validation_index + 1 - int(passed_test_partition)} of {len(partitions) - 1}.')

                status_counter = {
                    key: 0 for key in self.ARRIVAL_STATUSES.keys()}
                day_counter = {str(day_k): status_counter.copy()
                               for day_k in range(1, 8)}
                airline_counter = {aline_k: status_counter.copy()
                                   for aline_k in seen_carriers}
                src_counter = {src_k: status_counter.copy()
                               for src_k in seen_airports}
                dst_counter = src_counter.copy()
                dep_time_counter = {dep_k: status_counter.copy()
                                    for dep_k in self.DEP_TIMES}
                src_tmp_counter = {tmp_k: status_counter.copy()
                                   for tmp_k in self.TEMP_KEYS}
                dst_tmp_counter = src_tmp_counter.copy()
                src_wind_counter = {wnd_k: status_counter.copy()
                                    for wnd_k in self.WIND_KEYS}
                dst_wind_counter = src_wind_counter.copy()

                training_range = [i for i in range(data_len) if not (
                    (test_start <= i < test_end) or (validation_start <= i < validation_end))]
                for i in training_range:
                    record = data[i]
                    status_k = None
                    if record['CANCELLED'] == '1.00':
                        status_k = f'cancel:{record["CANCELLATION_CODE"]}'
                    elif record['DIVERTED'] == '1.00':
                        status_k = 'divert'
                    else:
                        status_k = f'delay:{record["ARR_DELAY_GROUP"]}'

                    status_counter[status_k] += 1
                    day_counter[record['DAY_OF_WEEK']][status_k] += 1
                    airline_counter[record['OP_UNIQUE_CARRIER']][status_k] += 1
                    src_counter[record['ORIGIN_AIRPORT_ID']][status_k] += 1
                    dst_counter[record['DEST_AIRPORT_ID']][status_k] += 1
                    dep_time_counter[record['CRS_DEP_TIME']][status_k] += 1
                    src_tmp_counter[record['src_tavg']][status_k] += 1
                    dst_tmp_counter[record['dst_tavg']][status_k] += 1
                    src_wind_counter[record['src_wspd']][status_k] += 1
                    dst_wind_counter[record['dst_wspd']][status_k] += 1

            p_status = dict.fromkeys(self.ARRIVAL_STATUSES.keys(), 0)
            p_day = {key: p_status.copy() for key in day_counter.keys()}
            p_airline = {key: p_status.copy()
                         for key in airline_counter.keys()}
            p_src = {key: p_status.copy() for key in src_counter.keys()}
            p_dst = {key: p_status.copy() for key in dst_counter.keys()}
            p_dep_time = {key: p_status.copy()
                          for key in dep_time_counter.keys()}
            p_src_tmp = {key: p_status.copy()
                         for key in src_tmp_counter.keys()}
            p_dst_tmp = {key: p_status.copy()
                         for key in dst_tmp_counter.keys()}
            p_src_wnd = {key: p_status.copy()
                         for key in src_wind_counter.keys()}
            p_dst_wnd = {key: p_status.copy()
                         for key in dst_wind_counter.keys()}

            for k in k_values:
                for status_k in p_status.keys():
                    p_status[status_k] = self.laplace_smooth(
                        status_counter[status_k], data_len, len(p_status.keys()), k)
                    for key in p_day.keys():
                        p_day[key][status_k] = self.laplace_smooth(
                            day_counter[key][status_k], status_counter[status_k], len(p_day.keys()), k)

                    for key in p_airline.keys():
                        p_airline[key][status_k] = self.laplace_smooth(
                            airline_counter[key][status_k], status_counter[status_k], len(p_airline.keys()), k)

                    for key in p_src.keys():
                        p_src[key][status_k] = self.laplace_smooth(
                            src_counter[key][status_k], status_counter[status_k], len(p_src.keys()), k)

                    for key in p_dst.keys():
                        p_dst[key][status_k] = self.laplace_smooth(
                            dst_counter[key][status_k], status_counter[status_k], len(p_dst.keys()), k)

                    for key in p_dep_time.keys():
                        p_dep_time[key][status_k] = self.laplace_smooth(
                            dep_time_counter[key][status_k], status_counter[status_k], len(p_dep_time.keys()), k)

                    for key in p_src_tmp.keys():
                        p_src_tmp[key][status_k] = self.laplace_smooth(
                            src_tmp_counter[key][status_k], status_counter[status_k], len(p_src_tmp.keys()), k)

                    for key in p_dst_tmp.keys():
                        p_dst_tmp[key][status_k] = self.laplace_smooth(
                            dst_tmp_counter[key][status_k], status_counter[status_k], len(p_dst_tmp.keys()), k)

                    for key in p_src_wnd.keys():
                        p_src_wnd[key][status_k] = self.laplace_smooth(
                            src_wind_counter[key][status_k], status_counter[status_k], len(p_src_wnd.keys()), k)

                    for key in p_dst_wnd.keys():
                        p_dst_wnd[key][status_k] = self.laplace_smooth(
                            dst_wind_counter[key][status_k], status_counter[status_k], len(p_dst_wnd.keys()), k)

    def laplace_smooth(self, observations: int, total: int, dimension: int, k: int):
        return (observations + k) / (total + dimension * k)

    def fit_unsmoothed(self, dataset: list, test_start: int, test_end: int, validation_start: int, validation_end: int):
        raise NotImplementedError

    def fit(self, dataset: list, k: int, test_start: int, test_end: int, validation_start: int, validation_end: int, out_path: str = None):
        raise NotImplementedError

    def make_prediction(self, src_airport: int, dest_airport: int, operating_airline: str, departure_time: str):
        raise NotImplementedError
