# -*- coding: utf-8 -*-
"""astyle plugin for zazu"""
import zazu.styler
import zazu.util

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class AstyleStyler(zazu.styler.Styler):
    """Astyle plugin for code styling"""

    def style_file(self, file, verbose, dry_run):
        """Run astyle on a file"""
        args = ['astyle', '-v'] + self.options
        if dry_run:
            args.append('--dry-run')
        args.append(file)
        output = zazu.util.check_output(args)
        fix_needed = not output.startswith('Formatted  ')
        return file, fix_needed

    @staticmethod
    def default_extensions():
        return ['*.c',
                '*.cc',
                '*.cpp',
                '*.h',
                '*.hpp',
                '*.java']

    @staticmethod
    def type():
        return 'astyle'
