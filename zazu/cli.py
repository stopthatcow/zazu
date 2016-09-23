# -*- coding: utf-8 -*-
"""entry point for zazu"""
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

import click
import config
import git_helper
import subprocess
import zazu.build
import zazu.dev.commands
import zazu.repo.commands
import zazu.style
import zazu.upgrade


@click.group()
@click.version_option(version=zazu.__version__)
@click.pass_context
def cli(ctx):
    try:
        ctx.obj = config.Config(git_helper.get_root_path())
        required_zazu_version = ctx.obj.zazu_version_required()
        if required_zazu_version and required_zazu_version != zazu.__version__:
            click.echo('Warning: this repo has requested zazu {}, which doesn\'t match the installed version ({}). \
            Use "zazu upgrade" to fix this'.format(ctx.obj.zazu_version_required(), __version__))
    except subprocess.CalledProcessError:
        pass


cli.add_command(zazu.upgrade.upgrade)
cli.add_command(zazu.style.style)
cli.add_command(zazu.build.build)
cli.add_command(zazu.dev.commands.dev)
cli.add_command(zazu.repo.commands.repo)
