# -*- coding: utf-8 -*-
"""GoimportsStyler plugin for zazu."""
import zazu.styler

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2018'


class Styler(zazu.styler.Styler):
    """Goimports plugin for code styling."""

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return ['*.go']

    @staticmethod
    def type():
        """Return the name of this Styler."""
        return 'goimports'
