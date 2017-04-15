# -*- coding: utf-8 -*-
"""utility functions for zazu"""
try:
    import gnureadline
    assert gnureadline
except ImportError:
    try:
        import pyreadline
        assert pyreadline
    except ImportError:
        # Fall back to regular input
        pass
import builtins
import click
import fnmatch
import inquirer
import os
import subprocess

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def check_output(*args, **kwargs):
    try:
        return subprocess.check_output(*args, **kwargs)
    except OSError:
        raise_uninstalled(args[0][0])


FAIL_OK = [click.style('FAIL', fg='red', bold=True), click.style(' OK ', fg='green', bold=True)]


def format_checklist_item(tag, text, tag_formats=FAIL_OK):
    return '[{}] {}'.format(tag_formats[tag], text)


def prompt(text, default=None, expected_type=str):
    if default is not None:
        result = builtins.input('{} [{}]: '.format(text, default)) or default
    else:
        result = builtins.input('{}: '.format(text))
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
        response = inquirer.prompt(questions)
        if response is None:
            raise KeyboardInterrupt
        return response[' ']
    return choices[0]


def scantree(base_path, include_patterns, exclude_patterns, exclude_hidden=False):
    """List files recursively that match any of the include glob patterns but are not in an excluded pattern."""
    files = []
    exclude_dirs = set([os.path.normpath(e) for e in exclude_patterns])
    for dirName, subdirList, fileList in os.walk(base_path):
        for i in builtins.range(len(subdirList) - 1, -1, -1):
            sub = os.path.relpath(os.path.join(dirName, subdirList[i]), base_path)
            if sub in exclude_dirs or (exclude_hidden and sub[0] == '.'):
                del subdirList[i]
        for f in fileList:
            if (not exclude_hidden) or (f[0] != '.'):
                file = os.path.relpath(os.path.join(dirName, f), base_path)
                if any(fnmatch.fnmatch(file, i) for i in include_patterns):
                    if all(not fnmatch.fnmatch(file, e) for e in exclude_patterns):
                        files.append(file)
    return files


def pprint_list(data):
    """Formats list as a bulleted list string"""
    return '\n  - {}'.format('\n  - '.join(data))


def raise_uninstalled(pkg_name):
    """Prints a warning to std error for a missing package"""
    raise click.ClickException('{0} not found, install it via "apt-get install {0}" or "brew install {0}"'.format(pkg_name))
