# -*- coding: utf-8 -*-
"""entry point for zazu"""
import click
import os
import zazu.build
import zazu.config
import zazu.dev.commands
import zazu.release.commands
import zazu.repo.commands
import zazu.style
import zazu.tool.commands
import zazu.upgrade
import zazu.version

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@click.group()
@click.version_option(version=zazu.version.Version())
@click.option('-v', '--verbose', count=True)
@click.pass_context
def cli(ctx, verbose):
    ctx.obj = zazu.config.Config(os.getcwd())
    zazu.verbose_level = verbose

cli.add_command(zazu.upgrade.upgrade)
cli.add_command(zazu.style.style)
cli.add_command(zazu.build.build)
cli.add_command(zazu.dev.commands.dev)
cli.add_command(zazu.release.commands.release)
cli.add_command(zazu.repo.commands.repo)
cli.add_command(zazu.tool.commands.tool)
