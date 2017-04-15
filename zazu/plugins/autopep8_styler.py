# -*- coding: utf-8 -*-
"""Autopep8Styler plugin for zazu"""
import concurrent.futures
import multiprocessing
import os
import zazu.styler
import zazu.util

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class Autopep8Styler(zazu.styler.Styler):
    """Autopep8 plugin for code styling. Executes in calls to autopep8 in parallel for speed"""

    def run(self, files, verbose, dry_run, working_dir):
        """Concurrently dispatches multiple workers to perform autopep8"""
        abs_files = [os.path.join(working_dir, f) for f in files]
        with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures = {executor.submit(Autopep8Styler.autopep8_file, f, self.options, verbose, dry_run): f for f in abs_files}
            for future in concurrent.futures.as_completed(futures):
                file_path, violation = future.result()
                yield os.path.relpath(file_path, working_dir), violation

    @staticmethod
    def autopep8_file(file, options, verbose, dry_run):
        """checks a single file to see if it is within style guidelines and optionally fixes it"""
        args = ['autopep8']
        args += options

        check_args = args + ['--diff', file]
        fix_args = args + ['--in-place', file]

        fix_needed = True
        if dry_run or verbose:
            output = zazu.util.check_output(check_args)
            if not output:
                fix_needed = False
        if not dry_run and fix_needed:
            zazu.util.check_output(fix_args)
        return file, fix_needed

    @staticmethod
    def default_extensions():
        return ['*.py']

    @staticmethod
    def type():
        return 'autopep8'
