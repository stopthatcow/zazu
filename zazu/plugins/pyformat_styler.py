# -*- coding: utf-8 -*-
"""PyformatStyler plugin for zazu."""
import zazu.styler
import zazu.util
zazu.util.lazy_import(locals(), [
    'subprocess',
    'os',
    'tempfile'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class PyformatStyler(zazu.styler.Styler):
    """Pyformat plugin for code styling."""

    def style_string(self, string):
        """Fix a string to be within style guidelines."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(string)
            tmp_file = f.name
        args = ['pyformat', '-i'] + self.options + [tmp_file]
        subprocess.check_output(args)
        with open(tmp_file, 'r') as f:
            yield f.read()
        os.remove(tmp_file)

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return ['*.py']

    @staticmethod
    def type():
        """Return the name of this Styler."""
        return 'pyformat'
