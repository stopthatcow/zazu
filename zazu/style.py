# -*- coding: utf-8 -*-
"""Style functions for zazu."""
import zazu.config
import zazu.git_helper
import zazu.styler
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'difflib',
    'functools',
    'os',
    'threading',
    'sys'
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


default_exclude_paths = ['build',
                         'dependency',
                         'dependencies']


def read_file(path):
    """Read a file and return its contents as a string."""
    with open(path, 'r') as f:
        return f.read()


def write_file(path, _, styled_string):
    """Write styled_string string to a file."""
    with open(path, 'w') as f:
        return f.write(styled_string)


"""The git binary doesn't allow concurrent access, so serailize calls to it using a lock."""
git_lock = threading.Lock()


def stage_patch(path, input_string, styled_string):
    """Create a patch between input_string and output_string and add the patch to the git staging area.

    Args:
        path: the path of the file being patched.
        input_string: the current state of the file in the git stage.
        styled_string: the properly styled string to stage.

    """
    # If the input was the same as the current file contents, apply the styling locally and add it.
    if read_file(path) == input_string:
        write_file(path, '', styled_string)
        with git_lock:
            zazu.util.check_output(['git', 'add', path])
    else:
        # The file is partially staged. We must apply a patch to the staging area.
        input_lines = input_string.splitlines()
        styled_lines = styled_string.splitlines()
        patch = difflib.unified_diff(input_lines, styled_lines, 'a/' + path, 'b/' + path, lineterm='')
        patch_string = '\n'.join(patch) + '\n'
        if input_string[-1] != '\n':
            # This is to address a bizarre issue with git apply whereby if the staged file doesn't end in a newline,
            # the patch will fail to apply.
            raise click.ClickException('File "{}" must have a trailing newline'.format(path))
        with git_lock:
            zazu.util.check_popen(args=['git', 'apply', '--cached', '--verbose', '-'], stdin_str=patch_string)


def style_file(stylers, path, read_fn, write_fn):
    """Style a file.

    Args:
        styler: the styler to use to style the file.
        path: the file path.
        read_fn: function used to read in the file contents.
        write_fn: function used to write out the styled file, or None

    """
    input_string = read_fn(path)
    styled_string = input_string
    for styler in stylers:
        styled_string = styler.style_string(styled_string, path)
    violation = styled_string != input_string
    if violation and callable(write_fn):
        write_fn(path, input_string, styled_string)
    return path, stylers, violation


def styler_list(file, sets, keys):
    """Get the list of stylers to apply to a file based on the file set of each styler."""
    return [s for s in keys if file in sets[s]]


@click.command()
@zazu.config.pass_config
@click.option('-v', '--verbose', is_flag=True, help='print files that are dirty')
@click.option('--check', is_flag=True, help='only check the repo for style violations, do not correct them')
@click.option('--cached', is_flag=True, help='only examine/fix files that are staged for CI commit')
def style(config, verbose, check, cached):
    """Style repo files or check that they are valid style."""
    config.check_repo()
    file_count = 0
    violation_count = 0
    stylers = config.stylers()
    fixed_ok_tags = [click.style('FIXED', fg='red', bold=True), click.style(' OK  ', fg='green', bold=True)]
    tags = zazu.util.FAIL_OK if check else fixed_ok_tags
    with zazu.util.cd(config.repo_root):
        if stylers:
            if cached:
                staged_files = zazu.git_helper.get_touched_files(config.repo)
                read_fn = zazu.git_helper.read_staged
                write_fn = stage_patch
            else:
                read_fn = read_file
                write_fn = write_file
            if check:
                write_fn = None
            # Determine files for each styler.
            file_sets = {}
            styler_file_sets = {}
            all_files = set()
            for s in stylers:
                includes = tuple(s.includes)
                excludes = tuple(s.excludes)
                if (includes, excludes) not in file_sets:
                    files = set(zazu.util.scantree(config.repo_root,
                                                   includes,
                                                   excludes,
                                                   exclude_hidden=True))
                    if cached:
                        files = files.intersection(staged_files)
                    file_sets[(includes, excludes)] = files
                else:
                    files = file_sets[(includes, excludes)]
                styler_file_sets[s] = files
                all_files |= files

            work = [functools.partial(style_file, styler_list(f, styler_file_sets, stylers), f, read_fn, write_fn) for f in all_files]
            checked_files = zazu.util.dispatch(work)
            for f, stylers, violation in checked_files:
                if verbose:
                    click.echo(zazu.util.format_checklist_item(not violation,
                                                               text='({}) {}'.format(', '.join([s.name() for s in stylers]), f),
                                                               tag_formats=tags))
                    violation_count += violation
            if verbose:
                file_count = len(all_files)
                if check:
                    click.echo('{} files with violations in {} files'.format(violation_count, file_count))
                else:
                    click.echo('{} files fixed in {} files'.format(violation_count, file_count))
            sys.exit(-1 if check and violation_count else 0)
        else:
            click.echo('no style settings found')
