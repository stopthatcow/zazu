# -*- coding: utf-8 -*-
"""Autopep8Styler plugin for zazu."""
import zazu.styler

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


class Autopep8Styler(zazu.styler.Styler):
    """Autopep8 plugin for code styling."""

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return ['*.py']

    @staticmethod
    def type():
        """Return the name of this Styler."""
        return 'autopep8'

    @staticmethod
    def required_options():
        """Get options required to make autopep8 take input from stdin."""
        return ['-']
