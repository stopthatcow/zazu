# -*- coding: utf-8 -*-
"""style functions for zazu"""
import zazu.git_helper
import zazu.styler
import zazu.util
zazu.util.lazy_import(locals(), [
    'click'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


default_exclude_paths = ['build',
                         'dependency',
                         'dependencies']


@click.command()
@click.pass_context
@click.option('-v', '--verbose', is_flag=True, help='print files that are dirty')
@click.option('--check', is_flag=True, help='only check the repo for style violations, do not correct them')
@click.option('--dirty', is_flag=True, help='only examine files that are staged for CI commit')
def style(ctx, verbose, check, dirty):
    """Style repo files or check that they are valid style"""
    ctx.obj.check_repo()
    file_count = 0
    violation_count = 0
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
            checked_files = s.run(files, verbose, check, ctx.obj.repo_root)
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
