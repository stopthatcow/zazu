# -*- coding: utf-8 -*-
"""astyle plugin for zazu."""
import zazu.styler
import zazu.util

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class AstyleStyler(zazu.styler.Styler):
    """Astyle plugin for code styling."""

    def style_file(self, path, verbose, dry_run):
        """Check a single file to see if it is within style guidelines and optionally fix it."""
        args = ['astyle', '--formatted'] + self.options
        if dry_run:
            args.append('--dry-run')
        args.append(path)
        output = zazu.util.check_output(args)
        return path, bool(output)

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
