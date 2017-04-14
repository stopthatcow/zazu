# -*- coding: utf-8 -*-
"""Styler class for zazu"""

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class Styler(object):
    """Parent of all style plugins"""

    def __init__(self, options=[], excludes=[], includes=[]):
        self.options = options
        self.excludes = excludes
        self.includes = includes

    def run(self, files, config, check, working_dir):
        raise NotImplementedError('All style plugins must implement run()')

    @classmethod
    def from_config(cls, config, excludes, includes):
        obj = cls(config.get('options', []),
                  excludes + config.get('excludes', []),
                  includes + config.get('includes', []))
        return obj
