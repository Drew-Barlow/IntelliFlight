# IntelliFlight

IntelliFlight is an app designed to predict flight delays, cancellations, and diversions based on factors such as weather, operating airline, flight plan (source and destination), and departure date/time. Implemented in Python, it is powered by the Naïve Bayesian Network machine learning model.


## Building the Test Environment

This app utilizes the Python virtual environment system to create and maintain a test environment isolated from the host system's Python installation and installed packages. To create the virtual environment in the directory `./.venv` , execute the following:

```
python -m venv .venv
```

Next, follow the steps in ["Activating & Deactivating the Test Environment](#Activating-&-Deactivating-the-Test-Environment) to enter the virtual environment. Finally, install the app and its dependencies in the virtual environment by running the following in the root project directory:

```
pip install -r requirements.txt
pip install -e .
```

The second command above will install the app in editable mode, meaning that the installation will point to the project directory, allowing the app's files to be modified without necessitating reinstallation.

To remove the virtual environment, delete the `.venv` folder. Virtual environments are non-portable; to move the environment, or if the project directory is moved, delete the `.venv` folder and repeat the above process in the new location.

NOTE: These steps have been tested on Windows only. For other platforms, see the Python documentation on virtual environments [here](https://docs.python.org/3/library/venv.html).


## Activating & Deactivating the Test Environment

From the root directory of the project, execute one of the following commands:

- PowerShell: `.\.venv\Scripts\Activate.ps1`
- Windows cmd.exe: `.\.venv\Scripts\activate.bat`

Upon activating the environment, `(.venv)` will be prepended to the console prompt to indicate that it is active, and directories containing the virtual environment's binaries will be prepended to the local `PATH`.

To deactivate the virtual environment and return to the normal environment, run the `deactivate` command within the virtual environment.


## Running Unit Tests

This project utilizes the [pytest](https://docs.pytest.org/en/latest/) framework for unit testing. All required packages are included in `requirements.txt` and installed as part of the setup process described [above](#building-the-test-environment).

### Running All Tests

To run all unit tests, execute `pytest` in the root directory.

### Running a subset of tests

To run unit tests for a subset of software modules, execute `pytest -m <module-mark>`. Marks are as follows:

- `nws`: Test the `nws_manager` module
- `datautil`: Test the `datautil` module
- `dataset`: Test the `Dataset` model component
- `keymeta`: Test the `KeyMeta` model component
- `frequencies`: Test the `FrequencyCounter` model component
- `ptables`: Test the `ProbabilityTables` model component

To test multiple modules, use `-m "<mark> and <mark> and ..."`.

### Generating Coverage Reports

To generate a code coverage report, execute any of the previous test commands with the added flags `--cov=<python-module-path> --cov-report term-missing`. For example, to test the coverage of the `ptables` module by the `ptables` test suite, execute `pytest -m ptables --cov=intelliflight.models.components.ptables --cov-report term-missing`.


## Deploying Production App

To install the app for production use, run `pip install .` in the project root directory.


## Usage Instructions

In both the test and normal environments, the installed app can be run with `python -m intelliflight <arguments>`. Supported commands are as follows.

### Using the GUI

Running `python -m intelliflight` with no arguments will launch the GUI.

### Accessing Help

Running `python -m intelliflight -h` or `python -m intelliflight --help` will print the help screen. This screen will also print if invalid arguments are provided to any command.

### Training the Model

The model can be trained using the following command:
```
python -m intelliflight train [-h] -t PATH_TO_FLIGHT_DATA -p PARTITION_COUNT -s K_STEP -m MAX_K [-r RNG_SEED]
```
Run `python -m intelliflight train -h` for more information on each argument.

### Making predictions

Predictions can be made with a trained model using the following command:
```
python -m intelliflight predict [-h] -s SRC_AIRPORT -d DST_AIRPORT -D DAY_OF_WEEK -t DEP_TIME
```
Run `python -m intelliflight predict -h` for more information on each argument.

### Listing Input Mappings

Airports, airlines, and days of the week are passed into the above commands using IDs rather than human-readable descriptions or names. To view the mappings of IDs to human-readable name, run the following commands:

#### Airports

```
python -m intelliflight list airports
```

#### Airlines

```
python -m intelliflight list airlines
```

#### Days of the Week

```
python -m intelliflight list days
```
