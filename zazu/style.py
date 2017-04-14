# -*- coding: utf-8 -*-
"""style functions for zazu"""
import click
import os
import subprocess
import zazu.git_helper
import zazu.styler
import zazu.util

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"

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
    stylers = ctx.obj.stylers()
    if stylers:
        if dirty:
            dirty_files = zazu.git_helper.get_touched_files(ctx.obj.repo)
        # Run each styler
        for s in stylers:
            files = zazu.util.scantree(ctx.obj.repo_root,
                                       s.includes,
                                       s.excludes,
                                       exclude_hidden=True)
            if dirty:
                files = set(files).intersection(dirty_files)
            file_count += len(files)
            violations += s.run(files, check, ctx.obj.repo_root)
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
