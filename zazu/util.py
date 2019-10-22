# -*- coding: utf-8 -*-
"""Utility functions for zazu."""

try:
    import readline  # NOQA
except ImportError:
    # This will be available on Windows
    import pyreadline  # NOQA

try:
    import urllib.parse as urlparse  # NOQA
except ImportError:
    import urlparse  # NOQA

import zazu.imports
zazu.imports.lazy_import(locals(), [
    'builtins',
    'click',
    'concurrent.futures',
    'contextlib',
    'dict_recursive_update',
    'fnmatch',
    'PyInquirer',
    'multiprocessing',
    'os',
    'subprocess',
    'sys',
])
__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


def check_output(*args, **kwargs):
    """Like subprocess.check_output but raises an exception if the program cannot be found."""
    try:
        return subprocess.check_output(*args, **kwargs)
    except OSError:
        raise_uninstalled(args[0])


def call(*args, **kwargs):
    """Like subprocess.call but raise an exception if the program cannot be found."""
    try:
        return subprocess.call(*args, **kwargs)
    except OSError:
        raise_uninstalled(args[0])


def check_popen(args, stdin_str=None, *other_args, **kwargs):
    """Like subprocess.Popen but raises an exception if the program cannot be found.

    Args:
        args: passed to Popen.
        stdin_str: a str/bytes that will be sent to std input via communicate().
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
        raise_uninstalled(args[0])
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
    with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()*5) as executor:
        futures = {executor.submit(w): w for w in work}
        for future in concurrent.futures.as_completed(futures):
            yield future.result()


def async_do(call, *args, **kwargs):
    """Dispatch a call asynchronously and return the future.

    Args:
        fn: the function to call.
        *args: args to forward to fn.
        **kwargs: args to forward to fn

    Returns:
        the future for the return of the called function.

    """
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(call, *args, **kwargs)
    executor.shutdown(wait=False)
    return future


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


def pick(choices, message):
    """Interactively allow user to pick among a set of choices.

    Args:
        choices: list of possible choices.
        message: the message to display to the user.

    """
    if not choices:
        return None
    if len(choices) > 1:
        click.clear()
        questions = {
            'type': 'list',
            'name': ' ',
            'message': message,
            'choices': choices
        }
        response = PyInquirer.prompt(questions)
        if not response:
            raise KeyboardInterrupt
        return response[' ']
    return choices[0]


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
    return '\n  - {}'.format('\n  - '.join(str(x) for x in data))


def flatten_dict(d, separator='.', prefix=''):
    """Flatten nested dictionary.

    Transforms {'a': {'b': {'c': 5}, 'd': 6}} into {'a.b.c': 5, 'a.d': 6}

    Args:
        d (dist): nested dictionary to flatten.
        separator (str): the separator to use between keys.
        prefix (str): key prefix

    Returns:
        dict: a dictionary with keys compressed and separated by separator.

    """
    return {prefix + separator + k if prefix else k: v
            for kk, vv in d.items()
            for k, v in flatten_dict(vv, separator, kk).items()
            } if isinstance(d, dict) else {prefix: d}


def unflatten_dict(d, separator='.'):
    """Unflatten nested dictionary.

    Transforms {'a.b.c': 5, 'a.d': 6} into {'a': {'b': {'c': 5}, 'd': 6}}

    Args:
        d (dict): nested dictionary to flatten.
        separator (str): the separator to use between keys.
        prefix (str): key prefix

    Returns:
        dict: a expanded dictionary with keys uncompressed.

    """
    ret = dict()
    for key, value in d.items():
        parts = key.split(separator)
        d = ret
        for part in parts[:-1]:
            if part not in d:
                d[part] = dict()
            d = d[part]
        d[parts[-1]] = value
    return ret


def dict_get_nested(d, keys, alt_ret):
    """Get a nested dictionary entry given a list of keys.

    Equivalent to d[keys[0]][keys[1]]...etc.

    Args:
        d (dict): nested dictionary to search.
        keys (list): keys to search one by one.
        alt_ret: returned if the specified item is not found.

    Returns:
          item matching the chain of keys in d.

    """
    item = d.get(keys[0], alt_ret)
    for k in keys[1:]:
        item = item.get(k, alt_ret)
    return item


def dict_del_nested(d, keys):
    """Delete a nested dictionary entry given a list of keys.

    Equivalent to del d[keys[0]][keys[1]]...etc.

    Args:
        d (dict): nested dictionary to search.
        keys (list): keys to search one by one.

    Raises:
        KeyError: if the key couldn't be found in d.

    """
    item = d
    if keys:
        for k in keys[:-1]:
            item = item[k]
        del item[keys[-1]]


def dict_update_nested(d, update):
    """Update a nested dictionary given an update dictionary.

    Args:
        d (dict): dictionary to add the update to.
        update (dict): update to apply to the dictionary.

    """
    dict_recursive_update.recursive_update(d, update)


def raise_uninstalled(pkg_name):
    """Raise an exception for a missing package.

    Args:
        pkg_name (str): the package name that is missing.

    Raises:
        click.ClickException

    """
    raise click.ClickException('{0} not found'.format(pkg_name))


def warn(text):
    """Emits a red warning to stderr."""
    click.secho('Warning: {}'.format(text), fg='red', err=True)


def base_url(url):
    """Returns a normalized form of the base url."""
    parts = list(urlparse.urlparse(url))
    parts[2:] = [''] * 4  # Clear the non-base parts.
    return urlparse.urlunparse(parts)
