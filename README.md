# IntelliFlight

TODO: make proper readme later
[DESCRIPTION]

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

To generate a code coverage report, execute any of the previous test commands with the added flag `--cov=<python-module-path>`. For example, to test the coverage of the `ptables` module by the `ptables` test suite, execute `pytest -m ptables --cov=intelliflight.models.components.ptables`.


## Deploying Production App

To install the app for production use, run `pip install .` in the project root directory.


## Running the App

In both the test and normal environments, the installed app can be run with `python -m intelliflight <arguments>`. TODO: ADD INFO ABOUT ARGUMENTS




https://docs.pytest.org/en/7.2.x/explanation/goodpractices.html
https://blog.ionelmc.ro/2014/05/25/python-packaging/
https://packaging.python.org/en/latest/tutorials/packaging-projects/
https://docs.python.org/3/library/venv.html
https://pypi.org/project/pytest-cov/