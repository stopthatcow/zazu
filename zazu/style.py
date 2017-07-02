# -*- coding: utf-8 -*-
"""Style functions for zazu."""
import zazu.git_helper
import zazu.styler
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'difflib',
    'functools',
    'os',
    'subprocess',
    'tempfile'

])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


default_exclude_paths = ['build',
                         'dependency',
                         'dependencies']


class threadsafe_iter:
    """Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """

    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def next(self):
        with self.lock:
            return self.it.next()


def threadsafe_generator(f):
    """A decorator that takes a generator function and makes it thread-safe.
    """
    def g(*a, **kw):
        return threadsafe_iter(f(*a, **kw))
    return g


@threadsafe_generator
def file_contents_generator(files):
    for f in files:
        with open(f, 'r') as f:
            yield f.read()


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def write_file(path, _, styled_string):
    with open(path, 'w') as f:
        return f.write(styled_string)


def stage_patch(path, input_string, styled_string):
    """Create a patch between input_string and output_string and add the patch to the git staging area.

    Args:
        path: the path of the file being patched.
        input_string: the current state of the file in the git stage.
        styled_string: the properly styled string to stage.
    """
    input_lines = input_string.splitlines()
    styled_lines = styled_string.splitlines()
    patch = difflib.unified_diff(input_lines, styled_lines, 'a/' + path, 'b/' + path, lineterm='')
    patch_string = '\n'.join(patch) + '\n'
    p = subprocess.Popen(['git', 'apply', '--cached', '-'], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = p.communicate(patch_string)
    if p.returncode:
        raise CalledProcessError(str(stderr))
    # If the input was the same as the current file contents, apply the styling locally as well.
    if read_file(path) == input_string:
        write_file(path, _, styled_string)


@click.command()
@click.pass_context
@click.option('-v', '--verbose', is_flag=True, help='print files that are dirty')
@click.option('--check', is_flag=True, help='only check the repo for style violations, do not correct them')
@click.option('--cached', is_flag=True, help='only examine/fix files that are staged for CI commit')
def style(ctx, verbose, check, cached):
    """Style repo files or check that they are valid style."""
    ctx.obj.check_repo()
    file_count = 0
    violation_count = 0
    stylers = ctx.obj.stylers()
    if stylers:
        if cached:
            staged_files = zazu.git_helper.get_touched_files(ctx.obj.repo)
        # Run each Styler
        for s in stylers:
            files = zazu.util.scantree(ctx.obj.repo_root,
                                       s.includes,
                                       s.excludes,
                                       exclude_hidden=True)
            if cached:
                files = set(files).intersection(staged_files)
                read_fn = zazu.git_helper.read_staged
                write_fn = stage_patch
            else:
                read_fn = read_file
                write_fn = write_file
            if check:
                write_fn = None
            file_count += len(files)
            with zazu.util.cd(ctx.obj.repo_root):
                checked_files = zazu.util.dispatch([functools.partial(s.style_one, f, read_fn, write_fn) for f in files])
                for f, violation in checked_files:
                    if verbose:
                        click.echo(zazu.util.format_checklist_item(not violation, text='({}) {}'.format(s.type(), f)))
                    violation_count += violation
        if verbose:
            if check:
                click.echo('{} files with violations in {} files'.format(violation_count, file_count))
            else:
                click.echo('{} files fixed in {} files'.format(violation_count, file_count))
        ctx.exit(-1 if check and violation_count else 0)
    else:
        click.echo('no style settings found')
