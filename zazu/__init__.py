# -*- coding: utf-8 -*-
import pkg_resources

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"

version_file_path = pkg_resources.resource_filename('zazu', 'version.txt')

try:
    with open(version_file_path, 'r') as version_file:
        __version__ = version_file.readline().rstrip()
except IOError:
    __version__ = "unknown"


class ZazuException(Exception):
    """Parent of all Zazu errors"""
