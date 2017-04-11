# -*- coding: utf-8 -*-
import click.testing
import zazu.cli
import tests.conftest

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_cli(git_repo):
    dir = git_repo.working_tree_dir
    with conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'setup', 'hooks'])
        assert result.exit_code == 0
        assert zazu.git_helper.check_git_hooks(dir)
