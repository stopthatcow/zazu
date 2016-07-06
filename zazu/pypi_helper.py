# -*- coding: utf-8 -*-
"""core functions for zazu"""

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

import os
import filecmp
import shutil
import pkg_resources
import platform


def get_pypi_config_files():
    if "Windows" in platform.system():
        settings_file_path = os.path.join(os.path.expanduser("~"), 'pip', 'pip.ini')
    else:
        settings_file_path = os.path.join(os.path.expanduser("~"), '.pip', 'pip.conf')
    conf_file = pkg_resources.resource_filename('zazu', 'pypi/pip.conf')
    return conf_file, settings_file_path


def check_pypi_config():
    """Checks if the proper pypi config is in place"""
    conf_file, settings_file_path = get_pypi_config_files()
    if os.path.exists(settings_file_path):
        if not filecmp.cmp(conf_file, settings_file_path):
            raise IOError
        else:
            return True
    return False


def enforce_pypi_config():
    conf_file, settings_file_path = get_pypi_config_files()
    try:
        os.mkdir(os.path.dirname(settings_file_path))
    except OSError:
        pass
    shutil.copy(conf_file, settings_file_path)
