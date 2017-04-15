# -*- coding: utf-8 -*-
"""ClangFormatStyler plugin for zazu"""
import concurrent.futures
import multiprocessing
import os
import zazu.styler
import zazu.util

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class ClangFormatStyler(zazu.styler.Styler):
    """ClangFormat plugin for code styling. Executes in calls to clang-format in parallel for speed"""

    def run(self, files, verbose, dry_run, working_dir):
        """Concurrently dispatches multiple workers to perform clang_format_file"""
        abs_files = [os.path.join(working_dir, f) for f in files]
        with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures = {executor.submit(ClangFormatStyler.clang_format_file, f, self.options, verbose, dry_run): f for f in abs_files}
            for future in concurrent.futures.as_completed(futures):
                file_path, violation = future.result()
                yield os.path.relpath(file_path, working_dir), violation

    @staticmethod
    def clang_format_file(file, options, verbose, dry_run):
        """checks a single file to see if it is within style guidelines and optionally fixes it"""
        args = ['clang-format']
        args += options

        check_args = args + ['--output-replacements-xml', file]
        fix_args = args + ['-i', file]

        fix_needed = True
        if dry_run or verbose:
            output = zazu.util.check_output(check_args)
            replacements_indicator = '</replacement>'
            if replacements_indicator not in output:
                fix_needed = False
        if not dry_run and fix_needed:
            zazu.util.check_output(fix_args)
        return file, fix_needed

    @staticmethod
    def default_extensions():
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
        return 'clang-format'
