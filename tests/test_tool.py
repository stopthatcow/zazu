# -*- coding: utf-8 -*-
import click
import zazu.cli

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_tool_install_bad_tool():
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['tool', 'install', 'foo==1.2.3'])
    assert result.exit_code
    assert result.output == 'Error: Tool foo not found\n'


def test_tool_uninstall_bad_tool():
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['tool', 'uninstall', 'foo'])
    assert result.exit_code
    assert result.output == 'Error: Tool foo not found\n'
