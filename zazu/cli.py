# -*- coding: utf-8 -*-
"""Entry point for zazu."""
import click
import zazu.config
import zazu.dev.commands
import zazu.repo.commands
import zazu.style
import zazu.upgrade

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


@click.group()
@click.version_option(version=zazu.__version__)
def cli():
    """Entry point for zazu cli."""
    pass


def init():
    """Run on startup to allow zazu to be run as a module."""
    if __name__ == '__main__':
        cli()


cli.add_command(zazu.upgrade.upgrade)
cli.add_command(zazu.style.style)
cli.add_command(zazu.config.config)
cli.add_command(zazu.dev.commands.dev)
cli.add_command(zazu.repo.commands.repo)
init()
