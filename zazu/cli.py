# -*- coding: utf-8 -*-
"""Entry point for zazu."""
import click
import os
import zazu.build
import zazu.config
import zazu.dev.commands
import zazu.git_helper
import zazu.repo.commands
import zazu.style
import zazu.upgrade

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@click.group()
@click.version_option(version=zazu.__version__)
@click.pass_context
def cli(ctx):
    """Entry point for zazu cli."""
    ctx.obj = zazu.config.Config(zazu.git_helper.get_repo_root(os.getcwd()))


cli.add_command(zazu.upgrade.upgrade)
cli.add_command(zazu.style.style)
cli.add_command(zazu.build.build)
cli.add_command(zazu.dev.commands.dev)
cli.add_command(zazu.repo.commands.repo)

if __name__ == "__main__":
    cli()
