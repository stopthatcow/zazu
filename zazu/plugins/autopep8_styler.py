# -*- coding: utf-8 -*-
"""Autopep8Styler plugin for zazu"""
import zazu.styler
import zazu.util

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class Autopep8Styler(zazu.styler.Styler):
    """Autopep8 plugin for code styling."""

    def style_file(self, path, verbose, dry_run):
        """checks a single file to see if it is within style guidelines and optionally fixes it"""
        args = ['autopep8'] + self.options

        check_args = args + ['--diff', path]
        fix_args = args + ['--in-place', path]

        fix_needed = True
        if dry_run or verbose:
            output = zazu.util.check_output(check_args)
            if not output:
                fix_needed = False
        if not dry_run and fix_needed:
            zazu.util.check_output(fix_args)
        return path, fix_needed

    @staticmethod
    def default_extensions():
        return ['*.py']

    @staticmethod
    def type():
        return 'autopep8'
