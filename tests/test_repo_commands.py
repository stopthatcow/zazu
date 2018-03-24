# -*- coding: utf-8 -*-
import click.testing
import conftest
import git
import os
import ruamel.yaml as yaml
import zazu.cli
import zazu.git_helper


__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_init(repo_with_empty_zazu_file):
    dir = repo_with_empty_zazu_file.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'init'])
        print result.output
        assert result.exit_code == 0
        assert zazu.git_helper.check_git_hooks(dir)


def test_cleanup_no_develop(repo_with_empty_zazu_file):
    dir = repo_with_empty_zazu_file.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup'])
        assert result.exit_code != 0
        assert result.exception


def test_cleanup_no_config(repo_with_empty_zazu_file):
    dir = repo_with_empty_zazu_file.working_tree_dir
    with zazu.util.cd(dir):
        repo_with_empty_zazu_file.git.checkout('HEAD', b='develop')
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup'])
        assert result.exit_code != 0
        assert result.exception


def test_cleanup(repo_with_empty_zazu_file):
    dir = repo_with_empty_zazu_file.working_tree_dir
    with zazu.util.cd(dir):
        repo_with_empty_zazu_file.git.checkout('HEAD', b='develop')
        repo_with_empty_zazu_file.git.checkout('HEAD', b='feature/F00-1')
        with open('README.md', 'w') as f:
            f.write('foo')
        repo_with_empty_zazu_file.git.commit('-am', 'touch readme')
        repo_with_empty_zazu_file.git.checkout('master')
        repo_with_empty_zazu_file.git.merge('feature/F00-1')
        assert 'feature/F00-1' in zazu.git_helper.get_merged_branches(repo_with_empty_zazu_file, 'master')
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup', '-b', 'master', '-y'])
        print result.output
        assert result.exit_code == 0
        assert not result.exception
        assert 'feature/F00-1' not in zazu.git_helper.get_merged_branches(repo_with_empty_zazu_file, 'master')


def test_cleanup_remote(git_repo_with_local_origin, mocker):
    mocker.patch('zazu.repo.commands.get_closed_branches', return_value=['feature/F00-1'])
    git_repo = git_repo_with_local_origin
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        with open('zazu.yaml', 'a') as file:
            yaml.dump({'issueTracker': {'type': 'github',
                                        'owner': 'foo',
                                        'repo': 'bar'}}, file)
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
    tickets = list(zazu.repo.commands.descriptors_from_branches(['feature/foo-4', 'badly/formed'], require_type=True))
    assert len(tickets) == 1
    assert tickets[0].type == 'feature/'
    assert tickets[0].id == 'foo-4'
    assert tickets[0].description == ''


def test_get_closed_branches(mocker):
    def foo1_is_closed(tracker, ticket):
        return 'FOO-1' == ticket.id
    mocker.patch('zazu.repo.commands.ticket_is_closed', side_effect=foo1_is_closed)
    issue_tracker = mocker.Mock()
    result = zazu.repo.commands.get_closed_branches(issue_tracker, ['feature/FOO-1', 'feature/FOO-2'])
    assert result == ['feature/FOO-1']


def test_ticket_is_closed(mocker):
    descriptor = zazu.dev.commands.IssueDescriptor('feature', 'FOO-1', '')
    issue_tracker = mocker.Mock()
    issue_tracker.issue = mocker.Mock(side_effect=zazu.issue_tracker.IssueTrackerError)
    zazu.repo.commands.ticket_is_closed(issue_tracker, descriptor)
    issue_tracker.issue.assert_called_once_with(descriptor.id)


def test_clone(mocker, repo_with_empty_zazu_file):
    mocker.patch('git.Repo.clone_from', return_value=repo_with_empty_zazu_file)
    dir = repo_with_empty_zazu_file.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'clone', 'http://foo/bar/baz.git'])
        assert result.exit_code == 0
        assert not result.exception
    git.Repo.clone_from.assert_called_once()
    assert git.Repo.clone_from.call_args[0][0] == 'http://foo/bar/baz.git'
    assert 'baz' == git.Repo.clone_from.call_args[0][1]


def test_clone_hosted(mocker, repo_with_empty_zazu_file):
    mocker.patch('git.Repo.clone_from', return_value=repo_with_empty_zazu_file)
    mocker.patch('zazu.config.Config.default_scm_host', return_value='foo')
    mock_scm_host = mocker.patch('zazu.scm_host.ScmHost', autospec=True)
    mock_host_repo = conftest.dict_to_obj({'id': 'bar',
                                           'ssh_url': 'http://github.com/foo/bar.git'})
    mock_scm_host.repos = mocker.Mock(return_value=[mock_host_repo])

    mocker.patch('zazu.config.Config.scm_hosts', return_value={'foo': mock_scm_host})
    dir = repo_with_empty_zazu_file.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'clone', 'foo/bar'])
        assert result.exit_code == 0
    git.Repo.clone_from.assert_called_once()
    assert git.Repo.clone_from.call_args[0][0] == 'http://github.com/foo/bar.git'
    assert 'bar' == git.Repo.clone_from.call_args[0][1]
    # No matching repo.
    result = runner.invoke(zazu.cli.cli, ['repo', 'clone', 'foo/baz'])
    assert result.exit_code != 0
    # No matching host.
    result = runner.invoke(zazu.cli.cli, ['repo', 'clone', 'foo2/baz'])
    assert result.exit_code != 0


def test_clone_no_hosted_hosted(mocker, repo_with_empty_zazu_file):
    mocker.patch('zazu.config.Config.scm_hosts', return_value={})
    dir = repo_with_empty_zazu_file.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'clone', 'foo/bar'])
        assert result.exit_code != 0
        assert result.exception
        assert result.output.startswith('Error: Unable to clone foo/bar')


def test_clone_error(mocker, repo_with_empty_zazu_file):
    mocker.patch('git.Repo.clone_from', side_effect=git.GitCommandError('clone', 'Foo'))
    dir = repo_with_empty_zazu_file.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'clone', 'http://foo/bar/baz.git'])
        assert result.exit_code != 0
        assert result.exception
    git.Repo.clone_from.assert_called_once()
