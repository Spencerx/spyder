# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
#

"""
Script for running Spyder tests programmatically.
"""

# Standard library imports
import argparse
import os

# To activate/deactivate certain things for pytests only
# NOTE: Please leave this before any other import here!!
os.environ['SPYDER_PYTEST'] = 'True'

# Third party imports
# NOTE: This needs to be imported before any QApplication.
# Don't remove it or change it to a different location!
# pylint: disable=wrong-import-position
from qtpy import QtWebEngineWidgets  # noqa

from qtpy.QtCore import QThread
import pytest


# To run our slow tests only in our CIs
CI = bool(os.environ.get('CI', None))
RUN_SLOW = os.environ.get('RUN_SLOW', None) == 'true'


def run_pytest(run_slow=False, extra_args=None, remoteclient=False):
    """Run pytest tests for Spyder."""
    # Be sure to ignore subrepos and remoteclient plugin
    pytest_args = ['-vv', '-rw', '--durations=10', '--ignore=./external-deps',
                   '-W ignore::UserWarning']

    if CI:
        # Show coverage
        pytest_args += ['--cov=spyder', '--no-cov-on-fail', '--cov-report=xml']

        # To display nice tests resume in Azure's web page
        if os.environ.get('AZURE', None) is not None:
            pytest_args += ['--cache-clear', '--junitxml=result.xml']
    if run_slow or RUN_SLOW:
        pytest_args += ['--run-slow']
    # Allow user to pass a custom test path to pytest to e.g. run just one test
    if extra_args:
        pytest_args += extra_args

    if remoteclient:
        pytest_args += [
            '--container-scope=class',
            '--remote-client',
            '-c',
            'pytest_remoteclient.ini'
        ]
        os.environ["SPYDER_TEST_REMOTE_CLIENT"] = "true"
    else:
        pytest_args += ['--timeout=120', '--timeout_method=thread']

    print("Pytest Arguments: " + str(pytest_args))
    errno = pytest.main(pytest_args)

    # Disconnect all signal-slots connection of the main QThread just before
    # runtests.py exits. This prevents a SEGFAULT when the finished signal of
    # the main QThread is triggered. This is an issue in the PyQt6 bindings
    # (PySide6 is also affected).
    try:
        QThread.currentThread().disconnect()
    except TypeError:  # raised when no signals are connected
        pass

    # sys.exit doesn't work here because some things could be running in the
    # background (e.g. closing the main window) when this point is reached.
    # If that's the case, sys.exit doesn't stop the script as you would expect.
    if errno != 0:
        raise SystemExit(errno)


def main():
    """Parse args then run the pytest suite for Spyder."""
    test_parser = argparse.ArgumentParser(
        usage=('python runtests.py'
               '[-h] [--run-slow] [--remote-client] [pytest_args]'),
        description="Helper script to run Spyder's test suite")
    test_parser.add_argument('--run-slow', action='store_true', default=False,
                             help='Run the slow tests')
    test_parser.add_argument("--remote-client", action="store_true",
                             default=False, help="Run the remote client tests")
    test_args, pytest_args = test_parser.parse_known_args()
    run_pytest(run_slow=test_args.run_slow, extra_args=pytest_args,
               remoteclient=test_args.remote_client)


if __name__ == '__main__':
    main()
