# -*- coding: utf-8 -*-
"""style functions for zazu"""
import click
import concurrent.futures
import multiprocessing
import os
import subprocess
import zazu.git_helper
import zazu.util

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def autopep8_file(file, config, check):
    """checks a single file to see if it is within style guidelines and optionally fixes it"""
    ret = []
    args = ['autopep8']
    args += config.get('options', [])

    check_args = args + ['--diff', file]
    fix_args = args + ['--in-place', file]

    try:
        output = subprocess.check_output(check_args)
    except OSError:
        zazu.util.raise_uninstalled(args[0])
    if len(output):
        if not check:
            subprocess.check_output(fix_args)
        ret.append(file)
    return ret


def autopep8(files, config, check, working_dir):
    """Concurrently dispatches multiple workers to perform autopep8"""
    abs_files = [os.path.join(working_dir, f) for f in files]
    ret = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = {executor.submit(autopep8_file, f, config, check): f for f in abs_files}
        for future in concurrent.futures.as_completed(futures):
            ret += [os.path.relpath(f, working_dir) for f in future.result()]
    return ret


def astyle(files, config, check, working_dir):
    """Run astyle on a set of files"""
    ret = []
    if len(files):
        args = ['astyle', '-v']
        args += config.get('options', [])
        if check:
            args.append('--dry-run')
        args += [os.path.join(working_dir, f) for f in files]
        try:
            output = subprocess.check_output(args)
        except OSError:
            zazu.util.raise_uninstalled(args[0])
        needle = 'Formatted  '
        for l in output.split('\n'):
            if l.startswith(needle):
                ret.append(os.path.relpath(l[len(needle):], working_dir))
    return ret

default_astyle_paths = ['*.cc',
                        '*.cpp',
                        '*.hpp',
                        '*.c',
                        '*.h']
default_py_paths = ['*.py']
default_exclude_paths = ['build',
                         'dependency',
                         'dependencies']


@click.command()
@click.pass_context
@click.option('--check', is_flag=True, help='only check the repo for style violations, do not correct them')
@click.option('--dirty', is_flag=True, help='only examine files that are staged for CI commit')
def style(ctx, check, dirty):
    """Style repo files or check that they are valid style"""
    ctx.obj.check_repo()
    violations = []
    file_count = 0
    style_config = ctx.obj.style_config()
    if style_config:
        if dirty:
            dirty_files = zazu.git_helper.get_touched_files(ctx.obj.repo)
        exclude_paths = style_config.get('exclude', default_exclude_paths)
        # astyle
        astyle_config = style_config.get('astyle', None)
        if astyle_config is not None:
            includes = astyle_config.get('include', default_astyle_paths)
            files = zazu.util.scantree(ctx.obj.repo_root, includes, exclude_paths, exclude_hidden=True)
            if dirty:
                files = set(files).intersection(dirty_files)
            file_count += len(files)
            violations += astyle(files, astyle_config, check, ctx.obj.repo_root)

        # autopep8
        autopep8_config = style_config.get('autopep8', None)
        if autopep8_config:
            includes = autopep8_config.get('include', default_py_paths)
            files = zazu.util.scantree(ctx.obj.repo_root, includes, exclude_paths, exclude_hidden=True)
            if dirty:
                files = set(files).intersection(dirty_files)
            file_count += len(files)
            violations += autopep8(files, autopep8_config, check, ctx.obj.repo_root)
        if check:
            for v in violations:
                click.echo("Violation in: {}".format(v))
            click.echo('{} files with violations in {} files'.format(len(violations), file_count))
            ctx.exit(-1 if violations else 0)
        else:
            for v in violations:
                click.echo("Formatted: {}".format(v))
            click.echo('{} files fixed in {} files'.format(len(violations), file_count))
    else:
        click.echo('no style settings found')
