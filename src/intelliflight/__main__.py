import argparse
import csv
import json
import sys
from .models.bayes_net import Bayes_Net
from pathlib import Path
from pydoc import pager


def cli_yes_no_prompt(msg: str) -> bool:
    """Prompt the user for a y/n response with msg, returning True if 'y' is
    answered and False if 'n' is answered."""
    response = ''
    while not (response == 'y' or response == 'n'):
        response = input(msg).lower()

    return response == 'y'


def ranged_float(min: float, max: float, inclusive_start: bool, inclusive_end: bool) -> callable:
    """Argparse type representing a float between min and max."""
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
    """Argparse type representing a time string as hh:mm."""
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


class HelpfulParser(argparse.ArgumentParser):
    """ArgumentParser class that prints the help"""

    def error(self, message):
        """Print error message and raise exception so main() can handle it."""
        print(f'Error: {message}\n')
        raise Exception()

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
    type=str,
    dest='src_airport',
    help='Source airport BTS ID.'
)
predict_subparser.add_argument(
    '-d', '--dst-airport',
    required=True,
    type=str,
    dest='dst_airport',
    help='Destination airport BTS ID.'
)
predict_subparser.add_argument(
    '-D', '--day',
    required=True,
    dest='day',
    type=int,
    choices=range(1, 8),
    help='Day of week of departure.'
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
        'airlines',
        'days'
    ],
    help='Input mapping to list.'
)

if len(sys.argv) == 1:
    # TODO: Invoke GUI here.
    pass

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

        bayes = Bayes_Net()
        bayes.load_data(args.flight_path)
        k, accuracy = bayes.train_model(
            args.partition_count, args.k_step, args.max_k, args.rng_seed)
        print(
            f'Generated model parameters with k={k} and an estimated accuracy of {accuracy}%.')
        if cli_yes_no_prompt('Would you like to save this model? (y/n): '):
            bayes.export_parameters()

    elif sys.argv[1] == 'predict':
        print('TODO: Implement CLI prediction')

    elif sys.argv[1] == 'list':
        if args.input == 'days':
            help_entries = [
                'Listing days by ID...',
                '',
                '1: Monday',
                '2: Tuesday',
                '3: Wednesday',
                '4: Thursday',
                '5: Friday',
                '6: Saturday',
                '7: Sunday'
            ]
            print('\n'.join(help_entries))

        else:
            params_path = root_dir / 'data' / 'models' / 'bayes_net.model.json'
            if not params_path.exists():
                print('Error: The model must be trained to use this functionality.')
                exit()

            bayes = Bayes_Net(params_path)

            if args.input == 'airports':
                airports = bayes.key_meta.get_seen_airports()
                airport_map_path = root_dir / 'data' / 'maps' / 'airport_mappings.json'
                mappings = json.load(airport_map_path.open())
                mappings_pruned = [
                    f'{entry["desc"]}@{entry["bts_id"]}'
                    for entry in mappings
                    if entry['bts_id'] in airports
                ]
                max_bts_len = 0
                for entry in mappings_pruned:
                    current_bts = entry.split('@')[1]
                    if len(current_bts) > max_bts_len:
                        max_bts_len = len(current_bts)

                mappings_pruned.sort()
                help_entries = [
                    'Listing Airports by BTS ID...',
                    "Press [Enter] to proceed 1 line.",
                    "Press [Space] to proceed 1 page.",
                    "Press [q] to exit.",
                    ''
                ]
                for entry in mappings_pruned:
                    desc, bts = entry.split('@')
                    help_entries.append(
                        f'{(bts + ":").ljust(max_bts_len + 2, " ")}{desc}')

                pager('\n'.join(help_entries))

            else:
                # Airlines
                airlines = bayes.key_meta.get_seen_carriers()
                airline_map_path = root_dir / 'data' / 'maps' / 'L_UNIQUE_CARRIERS.csv'
                mappings = csv.DictReader(airline_map_path.open())
                mappings_pruned = [
                    f'{entry["Description"]}@{entry["Code"]}'
                    for entry in mappings
                    if entry['Code'] in airlines
                ]

                max_code_len = 0
                for entry in mappings_pruned:
                    current_code = entry.split('@')[1]
                    if len(current_code) > max_code_len:
                        max_code_len = len(current_code)

                mappings_pruned.sort()
                help_entries = [
                    'Listing Airlines by code...',
                    "Press [Enter] to proceed 1 line.",
                    "Press [Space] to proceed 1 page.",
                    "Press [q] to exit.",
                    ''
                ]
                for entry in mappings_pruned:
                    desc, code = entry.split('@')
                    help_entries.append(
                        f'{(code + ":").ljust(max_code_len + 2, " ")}{desc}')

                pager('\n'.join(help_entries))

    else:
        raise Exception(
            'Something went wrong! This branch should never be triggered.')


# x = Bayes_Net('data/models/bayes_net.model.json')
# x = Bayes_Net()
# x.load_data('data/historical/flights/T_ONTIME_MARKETING.csv')
# x.train_model(10, .02, .1, 33000897)
# x.export_parameters()
