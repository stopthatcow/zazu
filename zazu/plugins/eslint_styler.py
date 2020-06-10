# -*- coding: utf-8 -*-
"""ESLint plugin for zazu."""
import zazu.imports
zazu.imports.lazy_import(locals(), [
    'click',
    'json',
    'os',
    'subprocess'
])

__author__ = "Patrick Moore"
__copyright__ = "Copyright 2018"


class Styler(zazu.styler.Styler):
    """ESLint plugin for code styling."""

    def style_string(self, string, filepath):
        """Fix a string to be within style guidelines.

        Args:
            string (str): the string to style
            filepath (str): the filepath of the file being styled

        Returns:
            Styled string.

        """
        eslint = 'eslint'
        cwd = os.path.normpath(os.getcwd())
        dirname = os.path.normpath(os.path.dirname(filepath))
        loop_count = 0

        local_eslint = os.path.join('node_modules', 'eslint', 'bin', 'eslint.js')

        while True and loop_count < 100:
            loop_count = loop_count + 1
            maybe_eslint = os.path.join(dirname, local_eslint)

            if os.path.isfile(maybe_eslint):
                eslint = maybe_eslint
                break
            elif os.path.realpath(dirname) == cwd:
                # Stop searching for eslint above current working directory
                # An invalid filepath should break-out here
                break

            new_dirname = os.path.realpath(os.path.join(dirname, '..'))
            if dirname == new_dirname:
                # Stop searching when dirname hits the system root
                break
            dirname = new_dirname

        if loop_count >= 100:
            raise click.ClickException('Unable to find eslint.js')

        args = [eslint, '-f', 'json', '--fix-dry-run', '--stdin', '--stdin-filename', filepath] + self.options
        try:
            p = subprocess.Popen(args=args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            results, _ = p.communicate(string)
        except OSError:
            raise click.ClickException('Unable to find {}'.format(args[0]))

        return json.loads(results)[0].get('output', string)

    @staticmethod
    def default_extensions():
        """Return the list of file extensions that are compatible with this Styler."""
        return ['*.js']

    @staticmethod
    def type():
        """Return the string type of this Styler."""
        return 'eslint'
