# -*- coding: utf-8 -*-
"""DocformatterStyler plugin for zazu."""
import zazu.styler
import zazu.util
zazu.util.lazy_import(locals(), [
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2018"


class DocformatterStyler(zazu.styler.Styler):
    """Docformatter plugin for code styling."""

    def style_string(self, string):
        """Fix a string to be within style guidelines."""
        args = ['docformatter'] + self.options + ['-']
        return zazu.util.check_popen(args=args, stdin_str=string)

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return ['*.py']

    @staticmethod
    def type():
        """Return the name of this Styler."""
        return 'docformatter'
