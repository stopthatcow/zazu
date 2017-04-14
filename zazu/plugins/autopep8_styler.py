# -*- coding: utf-8 -*-
"""Autopep8Styler plugin for zazu"""
import concurrent.futures
import multiprocessing
import os
import subprocess
import zazu.styler

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class Autopep8Styler(zazu.styler.Styler):
    """Autopep8 plugin for code styling. Executes in calls to autopep8 in parallel for speed"""
    def run(self, files, check, working_dir):
        """Concurrently dispatches multiple workers to perform autopep8"""
        abs_files = [os.path.join(working_dir, f) for f in files]
        ret = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures = {executor.submit(Autopep8Styler.autopep8_file, f, self.options, check): f for f in abs_files}
            for future in concurrent.futures.as_completed(futures):
                ret += [os.path.relpath(f, working_dir) for f in future.result()]
        return ret

    @staticmethod
    def autopep8_file(file, options, check):
        """checks a single file to see if it is within style guidelines and optionally fixes it"""
        ret = []
        args = ['autopep8']
        args += options

        check_args = args + ['--diff', file]
        fix_args = args + ['--in-place', file]

        try:
            output = subprocess.check_output(check_args)
        except OSError:
            zazu.util.raise_uninstalled(args[0])
        if len(output):
            if not check:
                subprocess.check_output(fix_args)
            ret.append(file)
        return ret

    @staticmethod
    def default_extensions():
        return ['*.py']

    @staticmethod
    def type():
        return 'autopep8'
