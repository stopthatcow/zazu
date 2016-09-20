# -*- coding: utf-8 -*-
"""style functions for zazu"""

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

import click
import concurrent.futures
import glob2 as glob
import multiprocessing
import os
import subprocess
import zazu.git_helper


def autopep8_file(file, config, check):
    """checks a single file to see if it is within style guidelines and optionally fixes it"""
    ret = []
    args = ['autopep8']
    args += config.get('options', [])

    check_args = args + ['--diff', file]
    fix_args = args + ['--in-place', file]

    output = subprocess.check_output(check_args)
    if len(output):
        if not check:
            subprocess.check_output(fix_args)
        ret.append(file)
    return ret


def autopep8(files, config, check):
    """Concurrently dispatches multiple workers to perform autopep8"""
    ret = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = {executor.submit(autopep8_file, f, config, check): f for f in files}
        for future in concurrent.futures.as_completed(futures):
            ret += future.result()
    return ret


def astyle(files, config, check):
    """Run astyle on a set of files"""
    ret = []
    if len(files):
        args = ['astyle', '-v']
        args += config.get('options', [])
        if check:
            args.append('--dry-run')
        args += files
        try:
            output = subprocess.check_output(args)
        except OSError:
            raise click.ClickException('astyle not found, please install it with brew or apt-get and ensure it is on your path')
        needle = 'Formatted  '
        for l in output.split('\n'):
            if l.startswith(needle):
                ret.append(l[len(needle):])
    return ret


def find_files(directory, pattern='*'):
    if not os.path.exists(directory):
        raise ValueError("Directory not found {}".format(directory))

    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            if fnmatch.filter([full_path], pattern):
                matches.append(os.path.join(root, filename))
    return matches


def glob_with_excludes(pattern, exclude):
    """globs and then excludes certain paths"""
    files = glob.glob(pattern)

    for e in exclude:
        files = [x for x in files if not x.startswith(e)]
    return files


default_astyle_paths = [os.path.join('**', '*.cpp'),
                        os.path.join('**', '*.hpp'),
                        os.path.join('**', '*.c'),
                        os.path.join('**', '*.h')]
default_py_paths = [os.path.join('**', '*.py')]
default_exclude_paths = [os.path.join('build'),
                         os.path.join('dependency'),
                         os.path.join('dependencies')]


@click.command()
@click.pass_context
@click.option('--check', is_flag=True, help='only check the repo for style violations, do not correct them (exit with the number of violations)')
@click.option('--dirty', is_flag=True, help='only examine files that are staged for CI commit')
def style(ctx, check, dirty):
    """Style repo files or check that they are valid style"""
    # options are specified with respect to the repo root
    ctx.obj.check_repo()
    os.chdir(ctx.obj.repo_root)
    violations = []
    try:
        style_config = ctx.obj.project_config()['style']
    except KeyError:
        raise click.ClickException('no "style" settings found in {}'.format(PROJECT_FILE_NAME))
    if dirty:
        dirty_files = zazu.git_helper.get_touched_files(ctx.obj.repo)
    exclude_paths = style_config.get('exclude', default_exclude_paths)
    # astyle
    astyle_config = style_config.get('astyle', None)
    if astyle_config is not None:
        for f in astyle_config.get('include', default_astyle_paths):
            files = glob_with_excludes(f, exclude_paths)
            if dirty:
                files = set(files).intersection(dirty_files)
            violations += astyle(files, astyle_config, check)

    # autopep8
    autopep8_config = style_config.get('autopep8', None)
    if autopep8_config is not None:
        for f in autopep8_config.get('include', default_py_paths):
            files = glob_with_excludes(f, exclude_paths)
            if dirty:
                files = set(files).intersection(dirty_files)
            violations += autopep8(files, autopep8_config, check)
    if check:
        for v in violations:
            click.echo("Violation in: {}".format(v))
        click.echo('{} violations detected'.format(len(violations)))
        ctx.exit(len(violations))
    else:
        for v in violations:
            click.echo("Formatted: {}".format(v))
        click.echo('{} violations fixed'.format(len(violations)))
