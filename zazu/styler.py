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

    def __init__(self, command=None, options=None, excludes=None, includes=None):
        """Constructor.

        Args:
            options: list of flags to pass to the styler.
            excludes: list of file patterns to exclude from styling.
            includes: list of file patterns to include for styling.
        """
        self.options = [] if options is None else options
        self.excludes = [] if excludes is None else excludes
        self.includes = [] if includes is None else includes
        self.options += self.required_options()
        self.command = self.type() if command is None else command

    def style_string(self, string):
        """Fix a string to be within style guidelines.

        Args:
            string (str): the string to style

        Returns:
            Styled string.

        """
        args = [self.command] + self.options
        return zazu.util.check_popen(args=args, stdin_str=string)

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
        obj = cls(config.get('command', None),
                  config.get('options', []),
                  excludes + config.get('excludes', []),
                  includes + config.get('includes', []))
        return obj

    @staticmethod
    def required_options():
        """Options required to make the tool use stdin for input and output styled version to stdout"""
        return []

    @staticmethod
    def default_extensions():
        raise NotImplementedError('Must implement default_extensions()')

    @staticmethod
    def type():
        raise NotImplementedError('Must implement type()')

    def name(self):
        return self.command
