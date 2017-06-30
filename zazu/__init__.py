# -*- coding: utf-8 -*-
"""Package level defines for zazu."""
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class LazyVersion():
    """Lazily loads version information only when it is converted to a string."""

    def __str__(self):
        """Load version information from version.txt file."""
        import pkg_resources
        version_file_path = pkg_resources.resource_filename('zazu', 'version.txt')
        with open(version_file_path, 'r') as version_file:
            version = version_file.readline().rstrip()
        return version


__version__ = LazyVersion()


class ZazuException(Exception):
    """Parent of all Zazu errors."""

    def __init__(self, *args, **kwargs):
        """Forward all arguments to Exception."""
        Exception.__init__(self, *args, **kwargs)
