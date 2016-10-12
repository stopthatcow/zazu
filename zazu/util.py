# -*- coding: utf-8 -*-
"""utility functions for zazu"""

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

try:
    import gnureadline
except ImportError:
    # Fall back to regular raw_input
    pass
import inquirer
import click
import os
import fnmatch


def prompt(text, default=None, expected_type=str):
    if default is not None:
        result = raw_input('{} [{}]: '.format(text, default)) or default
    else:
        result = raw_input('{}: '.format(text))
    return expected_type(result)


def pick(choices, message):
    if len(choices) > 1:
        click.clear()
        questions = [
            inquirer.List(' ',
                          message=message,
                          choices=choices,
                          ),
        ]
        return inquirer.prompt(questions)[' ']
    return choices[0]


def scantree(base_path, include_patterns, exclude_patterns, exclude_hidden=False):
    """List files recursively that match any of the include glob patterns but are not in an excluded pattern."""
    files = []
    exclude_dirs = set([os.path.normpath(e) for e in exclude_patterns])
    for dirName, subdirList, fileList in os.walk(base_path):
        for i in xrange(len(subdirList) - 1, -1, -1):
            sub = os.path.relpath(os.path.join(dirName, subdirList[i]))
            if sub in exclude_dirs:
                del subdirList[i]
        for f in fileList:
            if (not exclude_hidden) or (f[0] != '.'):
                file = os.path.relpath(os.path.join(dirName, f))
                if any(fnmatch.fnmatch(file, i) for i in include_patterns):
                    if all(not fnmatch.fnmatch(file, e) for e in exclude_patterns):
                        files.append(file)
    return files


def pprint_list(data):
    """Formats list as a bulleted list string"""
    return '\n  - {}'.format('\n  - '.join(data))
