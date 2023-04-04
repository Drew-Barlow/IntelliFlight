import argparse
import csv
import json
import sys
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
        print('TODO: Implement CLI prediction')

    elif sys.argv[1] == 'list':
        # Print input mappings
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


# x = Bayes_Net('data/models/bayes_net.model.json')
# x = Bayes_Net()
# x.load_data('data/historical/flights/T_ONTIME_MARKETING.csv')
# x.train_model(10, .02, .1, 33000897)
# x.export_parameters()
