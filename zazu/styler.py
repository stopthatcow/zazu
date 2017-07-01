# -*- coding: utf-8 -*-
"""Styler class for zazu."""
import zazu.util
zazu.util.lazy_import(locals(), [
    'functools',
    'os'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class Styler(object):
    """Parent of all style plugins."""

    def __init__(self, options=[], excludes=[], includes=[]):
        """Constructor.

        Args:
            options: array of flags to pass to the styler.
            excludes: list of file patterns to exclude from styling.
            includes: list of file patterns to include for styling.
        """
        self.options = options
        self.excludes = excludes
        self.includes = includes

    def run(self, files, verbose, dry_run, working_dir):
        """Concurrently dispatches multiple workers to perform style_file.

        Args:
            files: list of files to style.
            verbose: if true, print style status.
            dry_run: if true, doesn't touch local files.
            working_dir: the base directory that files are located in.
        """
        abs_files = [os.path.join(working_dir, f) for f in files]
        work = [functools.partial(self.style_file, f, verbose, dry_run) for f in abs_files]
        for file_path, violation in zazu.util.dispatch(work):
            yield os.path.relpath(file_path, working_dir), violation

    def style_file(self, path, verbose, dry_run):
        """Style a single file.

        Args:
            path: absolute path to the file to style.
            verbose: if true, print style status.
            dry_run: if true, doesn't touch local files.

        Raises:
            NotImplementedError

        """
        raise NotImplementedError('All style plugins must implement style_file()')

    def style_string(self, string):
        """Style a string and return a diff of requested changes

        Args:
            string: the string to style

        Returns:
                A unified diff of requested changes or an empty string if no changes are requested.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError('All style plugins must implement style_string')

    @classmethod
    def from_config(cls, config, excludes, includes):
        """Create a Styler based on a configuration dictionary.

        Args:
            config: the configuration dictionary.
            excludes: patterns to exclude.
            includes: patterns to include.

        Returns:
            Styler with config options set.

        """
        obj = cls(config.get('options', []),
                  excludes + config.get('excludes', []),
                  includes + config.get('includes', []))
        return obj
