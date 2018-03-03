# -*- coding: utf-8 -*-
"""eslint plugin for zazu."""
import zazu.styler
zazu.util.lazy_import(locals(), [
    'subprocess',
    'os',
    'tempfile'
])

__author__ = "Patrick Moore"
__copyright__ = "Copyright 2018"


class eslintStyler(zazu.styler.Styler):
    """ESLint plugin for code styling."""

    def style_string(self, string):
        """Fix a string to be within style guidelines."""
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".js")
        temp_path = temp.name
        args = ['eslint', '--fix'] + self.options + [temp_path]
        temp.write(string)
        temp.close()
        try:
            subprocess.check_output(args)
        except subprocess.CalledProcessError:
            pass
        with open(temp_path, "r") as f:
            ret = f.read()
        os.remove(temp_path)
        return ret

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return ['*.js']

    @staticmethod
    def type():
        """Return the string type of this Styler."""
        return 'eslint'
