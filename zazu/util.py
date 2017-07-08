# -*- coding: utf-8 -*-
<<<<<<< HEAD
"""utility functions for zazu"""
<<<<<<< HEAD
import zazu.plugins
=======
"""Utility functions for zazu."""
>>>>>>> develop
=======
import platform
import zazu.plugins
>>>>>>> 05b94a4f11b189243a35b2b4e7c762401d155bbe

try:
    import readline  # NOQA
except ImportError:
    # This will be available on Windows
    import pyreadline  # NOQA


def lazy_import(scope, imports):
    """Declare a list of modules to import on their first use.

    Args:
        scope: the scope to import the modules into.
        imports: the list of modules to import.
    """
    class LazyImport(object):

        def __init__(self, **entries):
            self.__dict__.update(entries)
    import peak.util.imports
    assert peak.util.imports
    for i in imports:
        modules = i.split('.')
        import_mock = peak.util.imports.lazyModule(i)
        if len(modules) > 1:
            d = import_mock
            while len(modules) > 1:
                d = {modules.pop(): d}
            scope[modules[0]] = LazyImport(**d)
        else:
            scope[modules[0]] = import_mock


lazy_import(locals(), [
    'builtins',
    'click',
    'concurrent.futures',
    'contextlib',
    'fnmatch',
    'inquirer',
    'multiprocessing',
    'os',
    'subprocess',
    'straight'
])
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def check_output(*args, **kwargs):
    """Like subprocess.check_output but raises an exception if the program cannot be found."""
    try:
        return subprocess.check_output(*args, **kwargs)
    except OSError:
        raise_uninstalled(args[0][0])


def call(*args, **kwargs):
    """Like subprocess.call but raise an exception if the program cannot be found."""
    try:
        return subprocess.call(*args, **kwargs)
    except OSError:
        raise_uninstalled(args[0][0])


def check_popen(args, stdin_str='', *other_args, **kwargs):
    """Like subprocess.Popen but raises an exception if the program cannot be found.

    Args:
        args: passed to Popen.
        stdinput_str: a string that will be sent to std input via communicate().
        other_args: other arguments passed to Popen.
        kwargs: other kwargs passed to Popen.
    Raises:
        CalledProcessError: on non zero return from the child process.
        click.ClickException: if the program can't be found.

    """
    try:
        p = subprocess.Popen(args=args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             *other_args, **kwargs)
        stdout, stderr = p.communicate(stdin_str)
    except OSError:
        raise_uninstalled(args[0][0])
    if p.returncode:
        raise subprocess.CalledProcessError(p.returncode, args, stderr)
    return stdout


@contextlib.contextmanager
def cd(path):
    """Change directory context manager.

    Args:
        path: the path to change to.

    """
    prev_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_dir)


def dispatch(work):
    """Dispatch a list of callables in multiple threads and yields their returns.

    Args:
        work: the list of callables to execute.

    Yields:
        the results of the callables as they are finished.

    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = {executor.submit(w): w for w in work}
        for future in concurrent.futures.as_completed(futures):
            yield future.result()


FAIL_OK = [click.style('FAIL', fg='red', bold=True), click.style(' OK ', fg='green', bold=True)]


def format_checklist_item(tag, text, tag_formats=FAIL_OK):
    """Format a list item based on an enumerated set of tags.

    Args:
        tag (int): index into the tag_formats list.
        text (str): the checklist text to display.
        tag_formats (list of str): the possible states of the checklist.

    Returns (str):
        the checklist string.

    """
    return '[{}] {}'.format(tag_formats[tag], text)


def prompt(text, default=None, expected_type=str):
    """Prompt user for an input.

    Args:
        text (str): the text to display to the user.
        default (str): the default to return if the user doesn't provide input.
        expected_type (type): the type to cast the user's return to.

    Returns:
        user's input casted to expected_type or default if no inout is provided.

    """
    if default is not None:
        result = builtins.input('{} [{}]: '.format(text, default)) or default
    else:
        result = builtins.input('{}: '.format(text))
    return expected_type(result)


<<<<<<< HEAD
<<<<<<< HEAD
def pick(choices, message, allow_multiple=False):
    """select from a list of possibilities."""
=======
def pick(choices, message):
    """Interactively allow user to pick among a set of choices.

    Args:
        choices: list of possible choices.
        message: the message to display to the user.

    """
>>>>>>> develop
    if not choices:
        return None
    if allow_multiple:
        choices = [None] + choices
    if len(choices) > 1:
        click.clear()
        questions = [inquirer.List(' ', message=message, choices=choices)]
=======
def pick(choices, message, checkbox=False):
    if len(choices) > 1:
        click.clear()
        if not checkbox:
            questions = [
                inquirer.List(' ',
                              message=message,
                              choices=choices,
                              ),
            ]
        else:
            questions = [
                inquirer.Checkbox(' ',
                             message = message,
                             choices = choices,
                             ),
            ]

>>>>>>> 05b94a4f11b189243a35b2b4e7c762401d155bbe
        response = inquirer.prompt(questions)
        if response is None:
            raise KeyboardInterrupt
        return response[' ']


def pick_multiple(choices, message):
    """interactivly pick multiple items from a list of possibilities."""
    if not choices:
        return None
    click.clear()
    response = inquirer.prompt([inquirer.Checkbox(' ', message=message, choices=choices)])
    if response is None:
        raise KeyboardInterrupt
    return response[' ']

 
def scantree(base_path, include_patterns, exclude_patterns, exclude_hidden=False):
    """List files recursively that match any of the include glob patterns but are not in an excluded pattern.

    Args:
        base_path (str): the path to scan.
        include_patterns (str): list of glob patterns to include.
        exclude_patterns (str): list of glob patterns to exclude.
        exclude_hidden (bool): don't include hidden files if True.

    Returns:
        list of str: of file paths (relative to the base path) that match the input parameters.

    """
    files = []
    exclude_dirs = set([os.path.normpath(e) for e in exclude_patterns])
    for dirName, subdirList, fileList in os.walk(base_path):
        for i in builtins.range(len(subdirList) - 1, -1, -1):
            sub = os.path.relpath(os.path.join(dirName, subdirList[i]), base_path)
            if sub in exclude_dirs or (exclude_hidden and sub[0] == '.'):
                del subdirList[i]
        for f in fileList:
            if (not exclude_hidden) or (f[0] != '.'):
                file = os.path.relpath(os.path.join(dirName, f), base_path)
                if any(fnmatch.fnmatch(file, i) for i in include_patterns):
                    if all(not fnmatch.fnmatch(file, e) for e in exclude_patterns):
                        files.append(file)
    return files


def pprint_list(data):
    """Format list as a bulleted list string.

    Args:
        data (list): the list to pprint.

    Returns:
        str: a newline separated pretty printed list.

    """
    return '\n  - {}'.format('\n  - '.join(data))


def raise_uninstalled(pkg_name):
    """Raise an exception for a missing package.

    Args:
        pkg_name (str): the package name that is missing.

    Raises:
        click.ClickException

    """
    raise click.ClickException('{0} not found, install it via "apt-get install {0}" or "brew install {0}"'.format(pkg_name))


def get_plugin_list(plugin_subclass):
    """helper function to pull lists of plugins"""
    plugins = straight.plugin.load('zazu.plugins', subclasses=plugin_subclass)
    known_types = {p.type().lower(): p.from_config for p in plugins}
    return known_types.keys()
