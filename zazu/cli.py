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
    except subprocess.CalledProcessError:
        pass


cli.add_command(zazu.upgrade.upgrade)
cli.add_command(zazu.style.style)
cli.add_command(zazu.build.build)
cli.add_command(zazu.dev.commands.dev)
cli.add_command(zazu.repo.commands.repo)
