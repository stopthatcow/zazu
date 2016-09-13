# -*- coding: utf-8 -*-
"""core functions for zazu"""
from zazu import __version__
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

import click
import config
import git_helper
import build
import style
import pip
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


@cli.command()
@click.option('--version', default='', help='version to upgrade to or empty for latest')
def upgrade(version):
    """Upgrade Zazu using pip"""
    # TODO for now hard code lily URLs, in future lean on pip.conf for this
    return pip.main(['install', '--upgrade',
                     '--trusted-host', 'pypi.lily.technology',
                     '--index-url', 'http://pypi.lily.technology:8080/simple', 'zazu{}'.format(version)])


cli.add_command(style.style)
cli.add_command(build.build)
cli.add_command(dev.dev)
cli.add_command(repo.repo)
