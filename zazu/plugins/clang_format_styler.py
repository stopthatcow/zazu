# -*- coding: utf-8 -*-
"""ClangFormatStyler plugin for zazu."""
import zazu.styler
import zazu.util
zazu.util.lazy_import(locals(), [
    'subprocess'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class ClangFormatStyler(zazu.styler.Styler):
    """ClangFormat plugin for code styling."""

    def style_string(self, string):
        """Fix a string to be within style guidelines."""
        args = ['clang-format'] + self.options
        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(string)
        if p.returncode:
            raise subprocess.CalledProcessError(stderr)
        return stdout

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
