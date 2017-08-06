# -*- coding: utf-8 -*-
import click.testing
import git
import os
import tests.conftest
import yaml
import zazu.cli
import zazu.git_helper


__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_cli(git_repo):
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'setup', 'hooks'])
        assert result.exit_code == 0
        assert zazu.git_helper.check_git_hooks(dir)


def test_init():
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['repo', 'init'])
    assert result.exit_code != 0


def test_init_nohooks():
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['repo', 'init', '--nohooks'])
    assert result.exit_code != 0


def test_cleanup_no_develop(git_repo):
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup'])
        assert result.exit_code != 0
        assert result.exception


def test_cleanup_no_config(git_repo):
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        git_repo.git.checkout('HEAD', b='develop')
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup'])
        assert result.exit_code != 0
        assert result.exception


def test_cleanup(git_repo):
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
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


def test_cleanup_remote(git_repo_with_local_origin, mocker):
    mocker.patch('zazu.repo.commands.get_closed_branches', return_value=['feature/F00-1'])
    git_repo = git_repo_with_local_origin
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        with open('zazu.yaml', 'a') as file:
            file.write(yaml.dump({'issueTracker': {'type': 'github',
                                                   'owner': 'foo',
                                                   'repo': 'bar'}}))
        git_repo.git.checkout('HEAD', b='develop')
        git_repo.git.checkout('HEAD', b='feature/F00-1')
        with open('README.md', 'w') as f:
            f.write('foo')
        git_repo.git.commit('-am', 'touch readme')
        git_repo.git.checkout('master')
        git_repo.git.merge('feature/F00-1')
        git_repo.git.push('--all', 'origin')
        assert 'feature/F00-1' in zazu.git_helper.get_merged_branches(git_repo, 'origin/master')
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup', '-y', '-r'])
        assert result.exit_code == 0
        assert not result.exception
        assert 'feature/F00-1' not in zazu.git_helper.get_merged_branches(git_repo, 'origin/master')


def test_descriptors_from_branches():
    tickets = list(zazu.repo.commands.descriptors_from_branches(['feature/foo-4', 'badly/formed']))
    assert len(tickets) == 1
    assert tickets[0].type == 'feature'
    assert tickets[0].id == 'foo-4'
    assert tickets[0].description == ''


def test_get_closed_branches(mocker):
    mocker.patch('zazu.repo.commands.ticket_is_closed', side_effect=[True, False])
    issue_tracker = mocker.Mock()
    result = zazu.repo.commands.get_closed_branches(issue_tracker, ['feature/FOO-1', 'feature/FOO-2'])
    assert result == ['feature/FOO-1']


def test_ticket_is_closed(mocker):
    descriptor = zazu.dev.commands.IssueDescriptor('feature', 'FOO-1', '')
    issue_tracker = mocker.Mock()
    issue_tracker.issue = mocker.Mock(side_effect=zazu.issue_tracker.IssueTrackerError)
    zazu.repo.commands.ticket_is_closed(issue_tracker, descriptor)
    issue_tracker.issue.assert_called_once_with(descriptor.id)


def test_clone(mocker, git_repo):
    mocker.patch('git.Repo.clone_from', return_value=git_repo)
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'clone', 'http://foo/bar/baz.git'])
        assert result.exit_code == 0
        assert not result.exception
    git.Repo.clone_from.assert_called_once()
    assert git.Repo.clone_from.call_args[0][0] == 'http://foo/bar/baz.git'
    assert os.path.join(dir, 'baz') in git.Repo.clone_from.call_args[0][1]


def test_clone_error(mocker, git_repo):
    mocker.patch('git.Repo.clone_from', side_effect=git.GitCommandError('clone', 'Foo'))
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'clone', 'http://foo/bar/baz.git'])
        assert result.exit_code != 0
        assert result.exception
    git.Repo.clone_from.assert_called_once()


def test_repo_ci_no_config(repo_with_build_config):
    dir = repo_with_build_config.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'setup', 'ci'])
        assert result.exit_code != 0
        assert result.exception
