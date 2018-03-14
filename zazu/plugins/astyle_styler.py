# -*- coding: utf-8 -*-
"""AstyleStyler plugin for zazu."""
import zazu.styler

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class AstyleStyler(zazu.styler.Styler):
    """Astyle plugin for code styling."""

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this
        Styler."""
        return ['*.c',
                '*.cc',
                '*.cs',
                '*.cpp',
                '*.h',
                '*.hpp',
                '*.java']

    @staticmethod
    def type():
        """Return the string type of this Styler."""
        return 'astyle'
