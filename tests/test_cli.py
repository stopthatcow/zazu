# -*- coding: utf-8 -*-
import click.testing
import zazu.cli

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_cli():
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['--help'])
    assert result.exit_code == 0
