# -*- coding: utf-8 -*-
"""EsformatterStyler plugin for zazu."""
import zazu.styler

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2018'


class Styler(zazu.styler.Styler):
    """Esformatter plugin for code styling."""

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return ['*.js',
                '*.es',
                '*.es6']

    @staticmethod
    def type():
        """Return the name of this Styler."""
        return 'esformatter'
