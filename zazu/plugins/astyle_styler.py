# -*- coding: utf-8 -*-
"""astyle plugin for zazu"""
import os
import zazu.styler
import zazu.util

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class AstyleStyler(zazu.styler.Styler):
    """Astyle plugin for code styling"""

    def run(self, files, verbose, dry_run, working_dir):
        """Run astyle on a set of files"""
        violations = []
        if files:
            args = ['astyle', '-v']
            args += self.options
            if dry_run:
                args.append('--dry-run')
            args += [os.path.join(working_dir, f) for f in files]
            output = zazu.util.check_output(args)
            needle = b'Formatted  '
            for l in output.split(b'\n'):
                if l.startswith(needle):
                    violations.append(os.path.relpath(l[len(needle):], working_dir))
        for f in files:
            yield f, f in violations

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
