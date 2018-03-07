# -*- coding: utf-8 -*-
"""Styler class for zazu."""
import zazu.util
zazu.util.lazy_import(locals(), [
    'functools',
    'os'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class Styler(object):
    """Parent of all style plugins."""

    def __init__(self, options=None, excludes=None, includes=None):
        """Constructor.

        Args:
            options: list of flags to pass to the styler.
            excludes: list of file patterns to exclude from styling.
            includes: list of file patterns to include for styling.
        """
        self.options = [] if options is None else options
        self.excludes = [] if excludes is None else excludes
        self.includes = [] if includes is None else includes

    def style_string(self, string):
        """Style a string and return a diff of requested changes.

        Args:
            string: the string to style

        Returns:
                A unified diff of requested changes or an empty string if no changes are requested.

        Raises:
            NotImplementedError

        """
        raise NotImplementedError('All style plugins must implement style_string')

    @classmethod
    def from_config(cls, config, excludes, includes):
        """Create a Styler based on a configuration dictionary.

        Args:
            config: the configuration dictionary.
            excludes: patterns to exclude.
            includes: patterns to include.

        Returns:
            Styler with config options set.

        """
        obj = cls(config.get('options', []),
                  excludes + config.get('excludes', []),
                  includes + config.get('includes', []))
        return obj
