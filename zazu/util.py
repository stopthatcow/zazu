# -*- coding: utf-8 -*-
"""utility functions for zazu"""

try:
    import readline  # NOQA
except ImportError:
    # This will be available on Windows
    import pyreadline  # NOQA


def lazy_import(scope, imports):
    """Imports modules when they are used"""
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
    'subprocess'
])
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def check_output(*args, **kwargs):
    try:
        return subprocess.check_output(*args, **kwargs)
    except OSError:
        raise_uninstalled(args[0][0])


def call(*args, **kwargs):
    try:
        return subprocess.call(*args, **kwargs)
    except OSError:
        raise_uninstalled(args[0][0])


@contextlib.contextmanager
def cd(path):
    prev_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_dir)


def dispatch(work):
    """Dispatches a list of callables in multiple threads and yields their returns"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = {executor.submit(w): w for w in work}
        for future in concurrent.futures.as_completed(futures):
            yield future.result()


FAIL_OK = [click.style('FAIL', fg='red', bold=True), click.style(' OK ', fg='green', bold=True)]


def format_checklist_item(tag, text, tag_formats=FAIL_OK):
    return '[{}] {}'.format(tag_formats[tag], text)


def prompt(text, default=None, expected_type=str):
    if default is not None:
        result = builtins.input('{} [{}]: '.format(text, default)) or default
    else:
        result = builtins.input('{}: '.format(text))
    return expected_type(result)


def pick(choices, message):
    if not choices:
        return None
    if len(choices) > 1:
        click.clear()
        questions = [
            inquirer.List(' ',
                          message=message,
                          choices=choices,
                          ),
        ]
        response = inquirer.prompt(questions)
        if response is None:
            raise KeyboardInterrupt
        return response[' ']
    return choices[0]


def scantree(base_path, include_patterns, exclude_patterns, exclude_hidden=False):
    """List files recursively that match any of the include glob patterns but are not in an excluded pattern."""
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
    """Formats list as a bulleted list string"""
    return '\n  - {}'.format('\n  - '.join(data))


def raise_uninstalled(pkg_name):
    """Raises a exception for a missing package"""
    raise click.ClickException('{0} not found, install it via "apt-get install {0}" or "brew install {0}"'.format(pkg_name))
