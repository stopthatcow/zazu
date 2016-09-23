# -*- coding: utf-8 -*-
"""utility functions for zazu"""

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

import gnureadline


def prompt(text, default=None, expected_type=str):
    if default is not None:
        result = raw_input('{} [{}]: '.format(text, default)) or default
    else:
        result = raw_input('{}: '.format(text))
    return expected_type(result)
