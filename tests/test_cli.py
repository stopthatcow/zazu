# -*- coding: utf-8 -*-
import click.testing
import zazu.cli

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_cli():
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['--help'])
    assert result.exit_code == 0


def test_init(mocker):
    cli_mock = mocker.patch('zazu.cli.cli')
    mocker.patch.object(zazu.cli, "__name__", "__main__")
    zazu.cli.init()
    assert cli_mock.call_count == 1
