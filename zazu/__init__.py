# -*- coding: utf-8 -*-

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


verbose_level = 0


def echo(message, level=0):
    """Print to terminal"""
    if level <= verbose_level:
        print(message)


def info(message):
    """Echo out at level 1"""
    echo(message, level=1)


def debug(message):
    """Echo out at level 2"""
    echo(message, level=2)


class ZazuException(Exception):
    """Parent of all Zazu errors"""

    def __init___(self, error):
        Exception.__init__("Error: {}".format(error))
