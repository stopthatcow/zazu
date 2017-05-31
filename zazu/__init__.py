# -*- coding: utf-8 -*-

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class LazyVersion():

    def __str__(self):
        import pkg_resources
        version_file_path = pkg_resources.resource_filename('zazu', 'version.txt')
        with open(version_file_path, 'r') as version_file:
            version = version_file.readline().rstrip()
        return version


__version__ = LazyVersion()


class ZazuException(Exception):
    """Parent of all Zazu errors"""

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
