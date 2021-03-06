# -*- coding: utf-8 -*-
"""ClangFormatStyler plugin for zazu."""
import zazu.styler

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2017'


class Styler(zazu.styler.Styler):
    """ClangFormat plugin for code styling."""

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return ['*.c',
                '*.cc',
                '*.cpp',
                '*.h',
                '*.hpp',
                '*.java',
                '*.js',
                '*.proto']

    @staticmethod
    def type():
        """Return the name of this Styler."""
        return 'clang-format'
