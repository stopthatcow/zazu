# -*- coding: utf-8 -*-
"""utility functions for zazu"""

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

try:
    import gnureadline
except ImportError:
    # Fall back to regular raw_input
    pass
try:
    import getch
except ImportError:
    # Fall back to regular raw_input
    pass
import inquirer
import click


def prompt(text, default=None, expected_type=str):
    if default is not None:
        result = raw_input('{} [{}]: '.format(text, default)) or default
    else:
        result = raw_input('{}: '.format(text))
    return expected_type(result)


def pick(choices, message):
    click.clear()
    questions = [
        inquirer.List(' ',
                      message=message,
                      choices=choices,
                      ),
    ]
    return inquirer.prompt(questions)[' ']
