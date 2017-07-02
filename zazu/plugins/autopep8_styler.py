# -*- coding: utf-8 -*-
"""Autopep8Styler plugin for zazu."""
import zazu.styler
import zazu.util
zazu.util.lazy_import(locals(), [
    'subprocess'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class Autopep8Styler(zazu.styler.Styler):
    """Autopep8 plugin for code styling."""

    def style_string(self, string):
        """Fix a string to be within style guidelines."""
        args = ['autopep8'] + self.options + ['-']
        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(string)
        if p.returncode:
            raise subprocess.CalledProcessError(stderr)
        return stdout

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return ['*.py']

    @staticmethod
    def type():
        """Return the name of this Styler."""
        return 'autopep8'
