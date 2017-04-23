# -*- coding: utf-8 -*-
"""Styler class for zazu"""
import zazu.util
zazu.util.lazy_import(locals(), [
    'functools',
    'os'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class Styler(object):
    """Parent of all style plugins"""

    def __init__(self, options=[], excludes=[], includes=[]):
        self.options = options
        self.excludes = excludes
        self.includes = includes

    def run(self, files, verbose, dry_run, working_dir):
        """Concurrently dispatches multiple workers to perform style_file."""
        abs_files = [os.path.join(working_dir, f) for f in files]
        work = [functools.partial(self.style_file, f, verbose, dry_run) for f in abs_files]
        for file_path, violation in zazu.util.dispatch(work):
            yield os.path.relpath(file_path, working_dir), violation

    def style_file(self, path, verbose, dry_run):
        raise NotImplementedError('All style plugins must implement style_file()')

    @classmethod
    def from_config(cls, config, excludes, includes):
        obj = cls(config.get('options', []),
                  excludes + config.get('excludes', []),
                  includes + config.get('includes', []))
        return obj
