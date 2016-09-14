# -*- coding: utf-8 -*-
"""entry point for zazu"""
from zazu import __version__
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

import click
import config
import git_helper
import build
import style
import upgrade
import subprocess
from .dev import commands as dev
from .repo import commands as repo


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    try:
        ctx.obj = config.Config(git_helper.get_root_path())
    except subprocess.CalledProcessError:
        pass


cli.add_command(upgrade.upgrade)
cli.add_command(style.style)
cli.add_command(build.build)
cli.add_command(dev.dev)
cli.add_command(repo.repo)
