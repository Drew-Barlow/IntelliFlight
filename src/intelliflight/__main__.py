import argparse
import csv
from datetime import date, timedelta, datetime, time
import json
import sys

from intelliflight.util import datautil, nws_manager
from .models.bayes_net import Bayes_Net
from pathlib import Path
from pydoc import pager
from intelliflight.GUI import App


## HELPER FUNCTIONS ##


def cli_yes_no_prompt(msg: str) -> bool:
    """Prompt the user with `msg` and await a y/n response.

    `msg` will be printed in a loop until 'y' or 'n' is received as input.
    Input is case-insensitive, but no extraneous characters (e.g., 'yes')
    are acceptable.

    Returns:

    `True` if 'y'; `False` if 'n'
    """
    response = ''
    while not (response == 'y' or response == 'n'):
        response = input(msg).lower()

    return response == 'y'


def ranged_float(min: float, max: float, inclusive_start: bool, inclusive_end: bool) -> callable:
    """Argparse type representing a float within a set range.

    Positional Arguments:

    - min -- lower bound for the acceptable range of values
    - max -- upper bound for the acceptable range of values
    - inclusive_start -- whether `min` is itself an acceptable value
    - inclusive_end -- whether `max` is itself an acceptable value

    Returns:

    A function that can be passed to the `type` argument of
    `argparse.add_argument()`
    """
    def check_range(arg_val: float) -> float:
        """Function to check that the passed argument is in the range."""
        arg_f = None
        try:
            arg_f = float(arg_val)

        except ValueError:
            # Arg is not float
            raise argparse.ArgumentTypeError('Must be a float.')

        start_bound_satisfied = \
            (min <= arg_f) if inclusive_start else (min < arg_f)
        end_bound_satisfied = \
            (max >= arg_f) if inclusive_end else (max > arg_f)

        if not (start_bound_satisfied and end_bound_satisfied):
            start_char = '[' if inclusive_start else '('
            end_char = ']' if inclusive_end else ')'
            raise argparse.ArgumentTypeError(
                f'Must be in range {start_char}{min}, {max}{end_char}.')

        return arg_f

    return check_range


def time_str() -> callable:
    """Argparse type representing a time string as hh:mm.

    Hour and minute fields need not be padded to 2 characters each, but
    each must be integral. Additionally, splitting the input string with ':'
    must return exactly 2 tokens. The valid range for hours is [0,23]; the
    valid range for minutes is [0,59].

    Violation of the above conditions will result in an `ArgumentTypeError`.

    Returns:

    A function that can be passed to the `type` argument of
    `argparse.add_argument()`
    """
    def check_format(time: str) -> str:
        """Function to check that the passed argument is of correct format."""
        try:
            tokens = time.split(':')
            if len(tokens) != 2:
                raise argparse.ArgumentTypeError('Must be of format hh:mm')

            hour = int(tokens[0])
            if not (0 <= hour < 24):
                raise argparse.ArgumentTypeError(
                    'Hour must be in range [0,23].')

            minute = int(tokens[1])
            if not (0 <= hour < 60):
                raise argparse.ArgumentTypeError(
                    'Minute must be in range [0,59].')

            return f"{str(hour).rjust(2, '0')}{str(minute).rjust(2, '0')}"

        except ValueError:
            raise argparse.ArgumentTypeError(
                'Hour and minute must be integers.')

    return check_format


def date_str() -> callable:
    """Argparse type representing a date as YYYY-MM-DD.

    Month and day fields need not be padded to 2 characters each, but
    each must be integral. Additionally, splitting the input string with '-'
    must return exactly 3 tokens.

    Violation of the above conditions will result in an `ArgumentTypeError`.

    Returns:

    A function that can be passed to the `type` argument of
    `argparse.add_argument()`
    """
    def check_format(datestamp: str) -> date:
        """Function to check that the passed argument is of correct format."""
        try:
            tokens = datestamp.split('-')
            if len(tokens) != 3:
                raise argparse.ArgumentTypeError(
                    'Must be of format YYYY-MM-DD')

            year = int(tokens[0])
            if not (year >= date.today().year):
                raise argparse.ArgumentTypeError(
                    f'Year must be >= {date.today().year} (the current date).')

            month = int(tokens[1])
            if not (month >= date.today().month):
                raise argparse.ArgumentTypeError(
                    f'Month must be >= {date.today().month} (the current date).')

            day = int(tokens[2])
            if not (day >= date.today().day):
                raise argparse.ArgumentTypeError(
                    f'Day must be >= {date.today().day} (the current date).')

            return date.fromisoformat(datestamp)

        except ValueError:
            raise argparse.ArgumentTypeError(
                'Must be a valid date of format YYYY-MM-DD.')

    return check_format


class HelpfulParser(argparse.ArgumentParser):
    """ArgumentParser class designed to facilitate custom behavior when
    invalid arguments are provided.

    The `error()` method is overridden such that it will print an error
    message before raising a generic `Exception()`. Calls to `parse_args()`
    should be wrapped in a `try`-`except` block implementing custom behavior.
    """

    def error(self, message):
        """Print error message and raise exception so main() can handle it."""
        print(f'Error: {message}\n')
        raise Exception()


## Argparse Setup ##


# Setup argument parser
parser = HelpfulParser(
    prog="IntelliFlight",
    description="An app to predict flight delays, diversions, and cancellations.",
    epilog='Passing no arguments will launch the GUI.'
)
subparsers = parser.add_subparsers(help="Command to run.")

# Parser for training mode
train_subparser = subparsers.add_parser('train', help="Train the model.")
train_subparser.add_argument(
    '-t', '--training-data',
    required=True,
    type=str,
    dest='flight_path',
    help='Path to training flight data.'
)
train_subparser.add_argument(
    '-p', '--partitions',
    required=True,
    type=int,
    choices=range(3, 11),
    dest='partition_count',
    help='Number of partitions to use. Ranges from 3 to 10.'
)
train_subparser.add_argument(
    '-s', '--step',
    required=True,
    type=ranged_float(0, 1, False, True),
    dest='k_step',
    help='Interval between candidate Laplace smoothing values as a percentage of the training dataset length. In range (0,1].'
)
train_subparser.add_argument(
    '-m', '--max-k',
    required=True,
    type=ranged_float(0, 1, True, True),
    dest='max_k',
    help='Maximum Laplace smoothing value as a percentage of the training dataset length. In range [0,1].'
)
train_subparser.add_argument(
    '-r', '--rng-seed',
    required=False,
    type=int,
    dest='rng_seed',
    help='Seed for RNG used to shuffle data. Useful for debugging or generating consistent output.'
)

# Parser for prediction mode
predict_subparser = subparsers.add_parser('predict', help="Make a prediction.")
predict_subparser.add_argument(
    '-s', '--src-airport',
    required=True,
    type=int,
    dest='src_airport',
    help='Source airport BTS ID.'
)
predict_subparser.add_argument(
    '-d', '--dst-airport',
    required=True,
    type=int,
    dest='dst_airport',
    help='Destination airport BTS ID.'
)
predict_subparser.add_argument(
    '-a', '--airline',
    required=True,
    type=str,
    dest='carrier',
    help='Airline ID.'
)
predict_subparser.add_argument(
    '-D', '--date',
    required=True,
    dest='date',
    type=date_str(),
    help='Departure date in YYYY-MM-DD.'
)
predict_subparser.add_argument(
    '-t', '--time',
    required=True,
    type=time_str(),
    dest='dep_time',
    help='Departure time on a 24-hour clock in hh:mm format.'
)

# Parser for mapping listing mode
list_subparser = subparsers.add_parser(
    'list', help='List possible input mappings.')
list_subparser.add_argument(
    'input',
    type=str,
    choices=[
        'airports',
        'airlines'
    ],
    help='Input mapping to list.'
)


## App Logic ##


if len(sys.argv) == 1:
    # No command provided (agrv[0] is program name)
    # Launch GUI
    App().mainloop()

else:
    # Process command line args
    try:
        args = parser.parse_args(sys.argv[1:])

    except:
        if any([arg in '--help' for arg in sys.argv[1:]]):
            # User called -h or --help, so help is already printed.
            # Do nothing.
            pass

        # Print appropriate help screen
        elif sys.argv[1] == 'train':
            train_subparser.print_help()

        elif sys.argv[1] == 'predict':
            predict_subparser.print_help()

        elif sys.argv[1] == 'list':
            list_subparser.print_help()

        else:
            parser.print_help()

        exit()

    # Args successfully parsed

    root_dir = Path(__file__).parent.parent.parent

    if sys.argv[1] == 'train':
        if (root_dir / 'data' / 'models' / 'bayes_net.model.json').exists():
            # Give user a chance to back out if the model is already trained.
            if not cli_yes_no_prompt('The model has already been trained. Do you wish to continue? (y/n): '):
                exit()

        # Ensure that training data file exists
        if not Path(args.flight_path).exists():
            print(f'Error: File {args.flight_path} does not exist.')
            exit()

        # Train
        bayes = Bayes_Net()
        bayes.load_data(args.flight_path)
        k, accuracy = bayes.train_model(
            args.partition_count, args.k_step, args.max_k, args.rng_seed)
        print(
            f'Generated model parameters with k={k} and an estimated accuracy of {accuracy}%.')

        # Prompt user to save model
        if cli_yes_no_prompt('Would you like to save this model? (y/n): '):
            bayes.export_parameters()

    elif sys.argv[1] == 'predict':
        # Load model
        model_path = (root_dir / 'data' / 'models' / 'bayes_net.model.json')
        if not model_path.exists():
            print(
                f'Error: Model file {model_path.as_posix()} does not exist. Train the model first.')
            exit()

        bayes = Bayes_Net(model_path.as_posix())

        # Get departure time and check if it is within bounds
        current_date = datetime.now()
        # args.dep_time is 'hhmm', not 'hh:mm'
        # Splits:
        #   'YYYY-MM-DDT00:00:00' -> 'YYYY-MM-DD' ['T'] '00:00:00'
        #   'hhmm' -> 'hh'
        #   'hhmm' -> 'mm'
        dep_timestamp = datetime.fromisoformat(args.date.isoformat().split('T')[
                                               0] + f'T{args.dep_time[:2]}:{args.dep_time[2:]}:00')

        if not ((dep_timestamp - current_date) <
                timedelta(days=7, hours=0, minutes=0, seconds=0)):
            print('Error: Departure time must be within 7 days of the current time.')
            exit()

        # Check that src and dst differ
        if args.src_airport == args.dst_airport:
            print('Error: Origin and Destination cannot be the same.')
            exit()

        try:
            # Get weather data
            forecast_src = nws_manager.Forecaster((root_dir / 'data' / 'maps' / 'airport_mappings.json').as_posix(
            )).get_nws_forecast_from_bts(args.src_airport, dep_timestamp.isoformat())
            forecast_dst = nws_manager.Forecaster((root_dir / 'data' / 'maps' / 'airport_mappings.json').as_posix(
            )).get_nws_forecast_from_bts(args.dst_airport, dep_timestamp.isoformat())

            # Discretize data/arguments
            data_to_discretize = [
                {
                    "CRS_DEP_TIME": args.dep_time,
                    'src_tavg': float(forecast_src['temperature']),
                    'dst_tavg': float(forecast_dst['temperature']),
                    'src_wspd': float(forecast_src['windSpeed'].split(' ')[0]),
                    'dst_wspd': float(forecast_dst['windSpeed'].split(' ')[0])
                }
            ]
            datautil.discretize(data_to_discretize)
            data_to_discretize = data_to_discretize[0]

            # Make prediction
            status_k, probability = bayes.make_prediction(
                args.src_airport,
                args.dst_airport,
                args.carrier,
                dep_timestamp.isoweekday(),
                data_to_discretize['CRS_DEP_TIME'],
                data_to_discretize['src_tavg'],
                data_to_discretize['dst_tavg'],
                data_to_discretize['src_wspd'],
                data_to_discretize['dst_wspd']
            )

            # If status is a cancellation, add a prefix for readability
            prefix = 'Cancelled due to ' if status_k.find(
                'cancel:') == 0 else ''

            # Print result
            print(
                '\nPredicted outcome:  ' +
                f'{prefix}{bayes.key_meta.get_arrival_statuses()[status_k]}'
            )
            print(
                'Confidence:         ' +
                f'{round(probability * 100, 2)}%'
            )

        except ConnectionError:
            # Forecaster got a 500 error from NWS
            print(
                'Error: Cannot connect to National Weather Service. Try again later.')
            exit()

        except KeyError as e:
            # Forecaster threw an error on an unknown airport
            print(f'Error: {e}')
            exit()

        except ValueError as e:
            # make_prediction threw an error on a bad argument value
            print(
                f'Error: {e}')
            exit()

    elif sys.argv[1] == 'list':
        # Print input mappings
        params_path = root_dir / 'data' / 'models' / 'bayes_net.model.json'
        if not params_path.exists():
            # The model only supports predictions with airports/airlines
            # seen in training data. Therefore, mappings are specific to
            # trained model instances.
            print('Error: The model must be trained to use this functionality.')
            exit()

        # Initialize model from which mappings will be extracted
        bayes = Bayes_Net(params_path)

        if args.input == 'airports':
            # Get airport BTS IDs
            airports = bayes.key_meta.get_seen_airports()
            # Get airport mapping data
            airport_map_path = root_dir / 'data' / 'maps' / 'airport_mappings.json'
            mappings = json.load(airport_map_path.open())
            # Generate 'description@id' strings for airports in model
            mappings_pruned = [
                f'{entry["desc"]}@{entry["bts_id"]}'
                for entry in mappings
                if entry['bts_id'] in airports
            ]
            # Get length of longest ID value (used for spacing later)
            max_bts_len = 0
            for entry in mappings_pruned:
                current_bts = entry.split('@')[1]
                if len(current_bts) > max_bts_len:
                    max_bts_len = len(current_bts)

            # Sort airports alphabetically by name/description
            mappings_pruned.sort()

            help_entries = [
                'Listing Airports by BTS ID...',
                "Press [Enter] to proceed 1 line.",
                "Press [Space] to proceed 1 page.",
                "Press [q] to exit.",
                ''
            ]
            # Append 'ID: description' strings to help_entries
            # Use max length found previously to pad 'ID:' portion and
            # ensure consistent spacing between columns
            for entry in mappings_pruned:
                desc, bts = entry.split('@')
                help_entries.append(
                    f'{(bts + ":").ljust(max_bts_len + 2, " ")}{desc}')

            # Print paged output
            pager('\n'.join(help_entries))

        else:
            # Get airline codes
            airlines = bayes.key_meta.get_seen_carriers()
            # Get airline mapping data
            airline_map_path = root_dir / 'data' / 'maps' / 'L_UNIQUE_CARRIERS.csv'
            mappings = csv.DictReader(airline_map_path.open())
            # Generate 'description@code' strings for airlines in model
            mappings_pruned = [
                f'{entry["Description"]}@{entry["Code"]}'
                for entry in mappings
                if entry['Code'] in airlines
            ]

            # Get length of longest code
            max_code_len = 0
            for entry in mappings_pruned:
                current_code = entry.split('@')[1]
                if len(current_code) > max_code_len:
                    max_code_len = len(current_code)

            # Sort alphabetically by name/description
            mappings_pruned.sort()

            help_entries = [
                'Listing Airlines by code...',
                "Press [Enter] to proceed 1 line.",
                "Press [Space] to proceed 1 page.",
                "Press [q] to exit.",
                ''
            ]
            # Append 'Code: description' strings to help_entries
            # Use max length found previously to pad 'Code:' portion and
            # ensure consistent spacing between columns
            for entry in mappings_pruned:
                desc, code = entry.split('@')
                help_entries.append(
                    f'{(code + ":").ljust(max_code_len + 2, " ")}{desc}')

            # Print paged output
            pager('\n'.join(help_entries))

    else:
        # Command was not 'train', 'predict', or 'list'.
        # The try-except block and len(argv) == 1 check above should make it
        # impossible to enter this branch.
        raise Exception(
            'Something went wrong! This branch should never be triggered.')
