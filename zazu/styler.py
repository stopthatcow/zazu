# -*- coding: utf-8 -*-
"""Styler class for zazu."""
import zazu.util
zazu.util.lazy_import(locals(), [
    'functools',
    'os'
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


class Styler(object):
    """Parent of all style plugins."""

    def __init__(self, command=None, options=None, excludes=None, includes=None):
        """Constructor.

        Args:
            command (str): command to use when running the styler.
            options (list): flags to pass to the styler.
            excludes (list): file patterns to exclude from styling.
            includes (list): file patterns to include for styling.
        """
        self.command = self.type() if command is None else command
        self.options = [] if options is None else options
        self.excludes = [] if excludes is None else excludes
        self.includes = [] if includes is None else includes
        self.options += self.required_options()

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
            excludes (list): file patterns to exclude from styling.
            includes (list): file patterns to include for styling.

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
        """Options required to make the tool use stdin for input and output styled version to stdout."""
        return []

    @staticmethod
    def default_extensions():
        """Extensions that this styler can fix."""
        raise NotImplementedError('Must implement default_extensions()')

    @staticmethod
    def type():
        """Return the type of this styler."""
        raise NotImplementedError('Must implement type()')

    def name(self):
        """Get name of this styler."""
        return self.command
