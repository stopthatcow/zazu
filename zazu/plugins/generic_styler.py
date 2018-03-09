# -*- coding: utf-8 -*-
"""GenericStdinStyler plugin for zazu."""
import zazu.styler

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2018"


class GenericStdinStyler(zazu.styler.Styler):
    """GenericStdinStyler plugin for code styling."""

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return []

    @staticmethod
    def type():
        """Return the name of this Styler."""
        return 'stdin'
