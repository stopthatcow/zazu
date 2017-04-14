# -*- coding: utf-8 -*-
"""astyle plugin for zazu"""
import os
import subprocess
import zazu.styler
import zazu.util

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class AstyleStyler(zazu.styler.Styler):
    """Astyle plugin for code styling"""
    def run(self, files, check, working_dir):
        """Run astyle on a set of files"""
        ret = []
        if len(files):
            args = ['astyle', '-v']
            args += self.options
            if check:
                args.append('--dry-run')
            args += [os.path.join(working_dir, f) for f in files]
            try:
                output = subprocess.check_output(args)
            except OSError:
                zazu.util.raise_uninstalled(args[0])
            needle = 'Formatted  '
            for l in output.split('\n'):
                if l.startswith(needle):
                    ret.append(os.path.relpath(l[len(needle):], working_dir))
        return ret

    @staticmethod
    def default_extensions():
        return ['*.cc',
                '*.cpp',
                '*.hpp',
                '*.c',
                '*.h']

    @staticmethod
    def type():
        return 'astyle'
