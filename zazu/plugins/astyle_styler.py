# -*- coding: utf-8 -*-
"""astyle plugin for zazu."""
import zazu.styler
zazu.util.lazy_import(locals(), [
    'subprocess'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class AstyleStyler(zazu.styler.Styler):
    """Astyle plugin for code styling."""

    def style_string(self, string):
        """Fix a string to be within style guidelines."""
        args = ['astyle'] + self.options
        return zazu.util.check_popen(args=args, stdinput_str=string)

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
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
