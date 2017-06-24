# -*- coding: utf-8 -*-
import click.testing
import zazu.cli
import zazu.git_helper
import tests.conftest

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_cli(git_repo):
    dir = git_repo.working_tree_dir
    with tests.conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'setup', 'hooks'])
        assert result.exit_code == 0
        assert zazu.git_helper.check_git_hooks(dir)


def test_init():
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['repo', 'init'])
    assert result.exit_code != 0


def test_cleanup_no_develop(git_repo):
    dir = git_repo.working_tree_dir
    with tests.conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup'])
        assert result.exit_code != 0
        assert result.exception


def test_cleanup_no_config(git_repo):
    dir = git_repo.working_tree_dir
    with tests.conftest.working_directory(dir):
        git_repo.git.checkout('HEAD', b='develop')
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup'])
        assert result.exit_code != 0
        assert result.exception


def test_cleanup(git_repo):
    dir = git_repo.working_tree_dir
    with tests.conftest.working_directory(dir):
        git_repo.git.checkout('HEAD', b='develop')
        git_repo.git.checkout('HEAD', b='feature/F00-1')
        with open('README.md', 'w') as f:
            f.write('foo')
        git_repo.git.commit('-am', 'touch readme')
        git_repo.git.checkout('master')
        git_repo.git.merge('feature/F00-1')
        assert 'feature/F00-1' in zazu.git_helper.get_merged_branches(git_repo, 'master')
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup', '-b', 'master', '-y'])
        assert result.exit_code == 0
        assert not result.exception
        assert 'feature/F00-1' not in zazu.git_helper.get_merged_branches(git_repo, 'master')
