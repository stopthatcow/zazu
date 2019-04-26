# -*- coding: utf-8 -*-
"""DocformatterStyler plugin for zazu."""
import zazu.styler

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2018'


class Styler(zazu.styler.Styler):
    """Docformatter plugin for code styling."""

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return ['*.py']

    @staticmethod
    def type():
        """Return the name of this Styler."""
        return 'docformatter'

    @staticmethod
    def required_options():
        """Get options required to make docformatter use stdin."""
        return ['-']
