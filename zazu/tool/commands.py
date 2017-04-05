# -*- coding: utf-8 -*-
import click
import tool_helper

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@click.group()
def tool():
    """Manage tools that zazu is familiar with"""
    pass


@tool.command()
@click.option('--force-reinstall', help='forces reinstallation', is_flag=True)
@click.argument('spec', autocompletion=tool_helper.get_specs)
def install(spec, force_reinstall):
    """Install tools that zazu is familiar with"""
    tool_helper.install_spec(spec, force_reinstall, click.echo)


@tool.command()
@click.argument('spec')
def uninstall(spec):
    """Uninstall tools that zazu is familiar with"""
    tool_helper.uninstall_spec(spec, click.echo)
