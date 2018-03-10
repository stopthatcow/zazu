# -*- coding: utf-8 -*-
"""StdinStyler plugin for zazu."""
import zazu.styler

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2018"


class StdinStyler(zazu.styler.Styler):
    """StdinStyler plugin for code styling."""

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return []

    @staticmethod
    def type():
        """Return the name of this Styler."""
        return 'stdin'
