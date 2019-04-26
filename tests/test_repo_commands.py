# -*- coding: utf-8 -*-
import click.testing
import tests.conftest as conftest
import git
import os
import pytest
import re
import ruamel.yaml as yaml
import zazu.cli
import zazu.git_helper


__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_init(git_repo):
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'init'])
        assert result.exit_code == 0
        assert zazu.git_helper.check_git_hooks(dir)


def test_cleanup_no_develop(git_repo):
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup'])
        assert result.exit_code != 0
        assert 'unable to checkout "develop"' in result.output
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
        assert 'feature/F00-1' in zazu.git_helper.merged_branches(git_repo, 'master')
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup', '-b', 'master', '-y'])
        assert result.exit_code == 0
        assert not result.exception
        assert 'feature/F00-1' not in zazu.git_helper.merged_branches(git_repo, 'master')


def test_cleanup_remote(git_repo_with_local_origin, mocker):
    mocker.patch('zazu.repo.commands.get_closed_branches', return_value={'feature/F00-1'})
    git_repo = git_repo_with_local_origin
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        with open('zazu.yaml', 'a') as file:
            yaml.dump({'issue_tracker': {'type': 'github',
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
        assert 'feature/F00-1' in zazu.git_helper.merged_branches(git_repo, 'origin/master')
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'cleanup', '-y', '-r'])
        assert result.exit_code == 0
        assert not result.exception
        assert 'feature/F00-1' not in zazu.git_helper.merged_branches(git_repo, 'origin/master')


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
    assert result == {'feature/FOO-1'}


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
    assert 'baz' == git.Repo.clone_from.call_args[0][1]


def test_clone_hosted(mocker, git_repo):
    mocker.patch('git.Repo.clone_from', return_value=git_repo)
    mocker.patch('zazu.config.Config.default_scm_host', return_value='foo')
    mock_scm_host = mocker.patch('zazu.scm_host.ScmHost', autospec=True)
    mock_host_repo = conftest.dict_to_obj({'id': 'bar',
                                           'ssh_url': 'http://github.com/foo/bar.git'})
    mock_scm_host.repos = mocker.Mock(return_value=[mock_host_repo])

    mocker.patch('zazu.config.Config.scm_hosts', return_value={'foo': mock_scm_host})
    dir = git_repo.working_tree_dir
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


def test_clone_no_hosted_hosted(mocker, git_repo):
    mocker.patch('zazu.config.Config.scm_hosts', return_value={})
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'clone', 'foo/bar'])
        assert result.exit_code != 0
        assert result.exception
        assert result.output.startswith('Error: Unable to clone foo/bar')


def test_clone_error(mocker, git_repo):
    mocker.patch('git.Repo.clone_from', side_effect=git.GitCommandError('clone', 'Foo'))
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'clone', 'http://foo/bar/baz.git'])
        assert result.exit_code != 0
        assert result.exception
    git.Repo.clone_from.assert_called_once()


def test_branch_is_empty(git_repo):
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        assert zazu.repo.commands.branch_is_empty(git_repo, 'master', 'master')
        assert not zazu.repo.commands.branch_is_empty(git_repo, 'master', 'non_existent')
        git_repo.create_head('empty').checkout()
        git_repo.create_head('not_empty').checkout()
        tmp_file = os.path.join(dir, 'temp.txt')
        with open(tmp_file, 'w') as f:
            f.write('\n')
        git_repo.index.add([tmp_file])
        git_repo.index.commit('make this not empty')
        assert zazu.repo.commands.branch_is_empty(git_repo, 'empty', 'master')
        assert not zazu.repo.commands.branch_is_empty(git_repo, 'non_empty', 'master')


def test_tag_to_version():
    valid_versions = ['r1.2.3', '1.2.3', '1.2.3']
    for ver in valid_versions:
        assert '1.2.3' == zazu.repo.commands.tag_to_version(ver)
    assert '1.2.0' == zazu.repo.commands.tag_to_version('1.2')
    assert '1.0.0' == zazu.repo.commands.tag_to_version('1')


def test_sanitize_branch_name():
    assert 'feature-ZZ-333-foobar' == zazu.repo.commands.sanitize_branch_name('feature/ZZ-333_foobar')


def test_make_version_number():
    with pytest.raises(click.ClickException):
        semver = zazu.repo.commands.make_version_number('master', 1, '1.1', 'abcdef1')
    semver = zazu.repo.commands.make_version_number('master', None, '1.1', 'abcdef1')
    assert str(semver) == '1.1.0+sha.abcdef1.branch.master'
    semver = zazu.repo.commands.make_version_number('release/1.2', 1, None, 'abcdef1')
    assert str(semver) == '1.2.0-1+sha.abcdef1.branch.release-1.2'
    semver = zazu.repo.commands.make_version_number('hotfix/1.2.1', 1, None, 'abcdef1')
    assert str(semver) == '1.2.1-1+sha.abcdef1.branch.hotfix-1.2.1'
    semver = zazu.repo.commands.make_version_number('feature/name', 1, None, 'abcdef1')
    assert str(semver) == '0.0.0-1+sha.abcdef1.branch.feature-name'


def test_make_semver_tagged(git_repo):
    ver_re = re.compile(r'1\.2\.3\+sha\..*\.branch\.master')
    git_repo.git.tag('-a', '1.2.3', '-m', 'my message')
    version = zazu.repo.commands.make_semver(git_repo.working_tree_dir, None)
    assert ver_re.match(str(version))
    # Tag again, to ensure we sort by semver
    git_repo.git.tag('-a', '1.2.4', '-m', 'my message')
    version = zazu.repo.commands.make_semver(git_repo.working_tree_dir, None)
    assert str(version).startswith('1.2.4+')


def test_make_semver_empty_repo(empty_repo):
    with pytest.raises(click.ClickException):
        zazu.repo.commands.make_semver(empty_repo.working_tree_dir, 0)


VERSION_RE = re.compile(r'0\.0\.0-4\+sha\..*\.branch\.master')
PEP440_RE = re.compile(r'0\.0\.0.dev4\+sha\..*\.branch\.master')


def test_make_semver(git_repo):
    version = zazu.repo.commands.make_semver(git_repo.working_tree_dir, 4)
    assert VERSION_RE.match(str(version))
    pep440_version = zazu.repo.commands.pep440_from_semver(version)
    assert PEP440_RE.match(pep440_version)


def test_describe(mocker, git_repo):
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['repo', 'describe', '--prerelease=4'])
        assert result.exit_code == 0
        assert VERSION_RE.match(result.output)
        result = runner.invoke(zazu.cli.cli, ['repo', 'describe', '--prerelease=4', '--pep440'])
        assert result.exit_code == 0
        assert PEP440_RE.match(result.output)


def test_complete_repo(mocker):
    mocked_scm_host = mocker.Mock()
    mocked_repo = mocker.Mock()
    mocked_repo.id = 'repo_id'
    mocked_scm_host.repos = mocker.Mock(return_value=[mocked_repo])
    mocked_config = mocker.Mock()
    mocked_config.scm_hosts = mocker.Mock(return_value={'default': mocked_scm_host})
    mocker.patch('zazu.config.Config', return_value=mocked_config)
    assert zazu.repo.commands.complete_repo(None, [], '') == ['default/repo_id']
    assert zazu.repo.commands.complete_repo(None, [], 'repo') == ['default/repo_id']
    assert zazu.repo.commands.complete_repo(None, [], 'foo') == []
    # Test with unresponsive host.
    mocked_scm_host.repos = mocker.Mock(side_effect=IOError)
    assert zazu.repo.commands.complete_repo(None, [], '') == []
