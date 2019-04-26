# -*- coding: utf-8 -*-
import click
import click.testing
import os
import pytest
import ruamel.yaml as yaml
import zazu.cli
import zazu.config
import zazu.git_helper
import zazu.util

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@pytest.fixture()
def temp_user_config(tmp_dir):
    config = {'scm_host': {'gh': {'type': 'github', 'user': 'user'}}}
    path = os.path.join(tmp_dir, '.zazuconfig.yaml')
    with open(path, 'w') as file:
        yaml.dump(config, file)
    return path


@pytest.fixture()
def empty_user_config(tmp_dir):
    path = os.path.join(tmp_dir, '.zazuconfig.yaml')
    with open(path, 'w'):
        pass
    return path


@pytest.fixture()
def repo_with_invalid_issue_tracker(git_repo):
    root = git_repo.working_tree_dir
    config = {
        'issue_tracker': {
        }
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        yaml.dump(config, file)
    return git_repo


@pytest.fixture()
def repo_with_unknown_issue_tracker(git_repo):
    root = git_repo.working_tree_dir
    config = {
        'issue_tracker': {
            'type': 'foobar',
        }
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        yaml.dump(config, file)
    return git_repo


@pytest.fixture()
def repo_with_jira(git_repo):
    root = git_repo.working_tree_dir
    jira_config = {
        'issue_tracker': {
            'type': 'jira',
            'url': 'https://zazu.atlassian.net/',
            'project': 'TEST',
            'component': 'Zazu'
        }
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        yaml.dump(jira_config, file)
    return git_repo


def test_invalid_issue_tracker(repo_with_invalid_issue_tracker):
    cfg = zazu.config.Config(repo_with_invalid_issue_tracker.working_tree_dir)
    with pytest.raises(click.ClickException):
        cfg.issue_tracker()


def test_unknown_issue_tracker(repo_with_unknown_issue_tracker):
    cfg = zazu.config.Config(repo_with_unknown_issue_tracker.working_tree_dir)
    with pytest.raises(click.ClickException):
        cfg.issue_tracker()


def test_jira_config(repo_with_jira):
    cfg = zazu.config.Config(repo_with_jira.working_tree_dir)
    tracker = cfg.issue_tracker()
    assert tracker is not None
    assert tracker.type() == 'jira'


def test_check_repo(tmp_dir):
    cfg = zazu.config.Config(tmp_dir)
    with pytest.raises(click.UsageError):
        cfg.check_repo()


def test_missing_repo(tmp_dir):
    cfg = zazu.config.Config(tmp_dir)
    with pytest.raises(click.ClickException):
        cfg.project_config()


def test_missing_config_file_in_repo(git_repo):
    cfg = zazu.config.Config(git_repo.working_tree_dir)
    with pytest.raises(click.ClickException):
        cfg.project_config()


def test_missing_syntax_error(git_repo_with_bad_config):
    cfg = zazu.config.Config(git_repo_with_bad_config.working_tree_dir)
    with pytest.raises(click.ClickException):
        cfg.project_config()


def test_unknown_styler():
    uut = zazu.config.Config('')
    uut._project_config = {'style': [{'stylers': [{'type': 'foo'}]}]}
    with pytest.raises(click.ClickException):
        uut.stylers()


def test_unknown_scm_host():
    uut = zazu.config.Config('')
    uut._user_config = {'scm_host': {'gh': {'type': ''}}}
    with pytest.raises(click.ClickException):
        uut.scm_hosts()


def test_no_type_scm_host():
    uut = zazu.config.Config('')
    uut._user_config = {'scm_host': {'gh': {}}}
    with pytest.raises(click.ClickException):
        uut.scm_hosts()


def test_no_scm_host():
    uut = zazu.config.Config('')
    uut._user_config = {}
    with pytest.raises(click.ClickException):
        uut.scm_hosts()


def test_scm_host_repo(mocker, temp_user_config):
    mocker.patch('zazu.config.user_config_filepath', return_value=temp_user_config)
    uut = zazu.config.Config('')
    mock_scm_host = mocker.Mock('zazu.scm_host.ScmHost', autospec=True)
    mock_scm_host.repos = mocker.Mock(side_effect=IOError)
    uut._scm_hosts = {'foo': mock_scm_host}
    uut._default_scm_host = 'foo'
    assert uut.scm_host_repo('foo/bar') is None


def test_github_scm_host():
    uut = zazu.config.Config('')
    uut._user_config = {'scm_host': {'gh': {'type': 'github', 'user': 'user'}}}
    assert uut.scm_hosts()
    assert uut.scm_hosts()['gh']
    assert uut.default_scm_host() == 'gh'


def test_default_string_scm_host():
    uut = zazu.config.Config('')
    uut._user_config = {'scm_host': {'default': 'gh2',
                                     'gh': {'type': 'github', 'user': 'user'},
                                     'gh2': {'type': 'github', 'user': 'user'}}}
    assert len(uut.scm_hosts()) == 2
    assert uut.default_scm_host() == 'gh2'


def test_default_dict_scm_host():
    uut = zazu.config.Config('')
    uut._user_config = {'scm_host': {'default': {'type': 'github', 'user': 'user'},
                                     'gh': {'type': 'github', 'user': 'user'}}}
    assert len(uut.scm_hosts()) == 2
    assert uut.default_scm_host() == 'default'


def test_bad_default_scm_host():
    uut = zazu.config.Config('')
    uut._user_config = {'scm_host': {'default': 'foo',
                                     'gh': {'type': 'github', 'user': 'user'}}}
    with pytest.raises(click.ClickException) as e:
        assert uut.default_scm_host()
        assert str(e.value) == 'default scm_host \'foo\' not found'


def test_github_user_config(mocker, temp_user_config):
    mocker.patch('zazu.config.user_config_filepath', return_value=temp_user_config)
    uut = zazu.config.Config('')
    assert uut.scm_hosts()
    assert uut.scm_hosts()['gh']


def test_empty_user_config(mocker, empty_user_config):
    mocker.patch('zazu.config.user_config_filepath', return_value=empty_user_config)
    uut = zazu.config.Config('')
    with pytest.raises(click.ClickException) as e:
        uut.scm_hosts()


def test_no_issue_tracker():
    uut = zazu.config.Config('')
    uut._project_config = {}
    with pytest.raises(click.ClickException):
        uut.issue_tracker()


def test_no_code_reviewer():
    uut = zazu.config.Config('')
    uut._project_config = {}
    with pytest.raises(click.ClickException):
        uut.code_reviewer()


def test_valid_code_reviewer():
    uut = zazu.config.Config('')
    uut._project_config = {'code_reviewer': {'type': 'github'}}
    assert uut.code_reviewer()


def test_user_config_filepath():
    assert zazu.config.user_config_filepath() == os.path.join(os.path.expanduser("~"), '.zazuconfig.yaml')


def test_missing_user_config(mocker, tmp_dir):
    mocker.patch('zazu.config.user_config_filepath', return_value=tmp_dir)
    uut = zazu.config.Config('')
    assert uut.user_config() == {}


def test_config_bad_options(mocker, temp_user_config):
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['config'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['config', '--add'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['config', '--add', 'foo'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['config', '--add', '--unset'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['config', '--unset'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['config', '--list', 'foo'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['config', '--show-origin', 'foo'])
    assert result.exit_code != 0


def test_config_list(mocker, temp_user_config):
    mocker.patch('zazu.config.user_config_filepath', return_value=temp_user_config)
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['config', '--list'])
    assert result.output == '''scm_host.gh.type=github\nscm_host.gh.user=user\n'''
    assert result.exit_code == 0
    result = runner.invoke(zazu.cli.cli, ['config', 'scm_host.gh.user'])
    assert result.output == 'user\n'
    assert result.exit_code == 0


def test_config_add_unset(mocker, temp_user_config):
    mocker.patch('zazu.config.user_config_filepath', return_value=temp_user_config)
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['config', '--unset', 'scm_host.gh.user'])
    assert result.exit_code == 0
    result = runner.invoke(zazu.cli.cli, ['config', 'scm_host.gh.user'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['config', 'scm_host.gh.user', 'user'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['config', 'scm_host.gh.user'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['config', '--add', 'scm_host.gh.user', 'user'])
    assert result.exit_code == 0
    result = runner.invoke(zazu.cli.cli, ['config', 'scm_host.gh.user'])
    assert result.exit_code == 0


def test_config_create(mocker, tmp_dir):
    path = os.path.join(tmp_dir, '.zazuconfig.yaml')
    mocker.patch('zazu.config.user_config_filepath', return_value=path)
    assert not os.path.isfile(path)
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['config', '--list'])
    assert result.exit_code == 0
    assert os.path.isfile(path)


def test_branch_names(git_repo):
    with zazu.util.cd(git_repo.working_tree_dir):
        uut = zazu.config.Config('')
        assert uut.develop_branch_name() == 'develop'
        assert uut.master_branch_name() == 'master'


def test_alt_branch_names(git_repo):
    with zazu.util.cd(git_repo.working_tree_dir):
        with open('zazu.yaml', 'w') as file:
            config = {
                'branches': {'develop': 'alt_develop',
                             'master': 'alt_master'}
            }
            yaml.dump(config, file)
        uut = zazu.config.Config('')
        assert uut.develop_branch_name() == 'alt_develop'
        assert uut.master_branch_name() == 'alt_master'


def test_complete_param(mocker, temp_user_config):
    mocker.patch('zazu.config.user_config_filepath', return_value=temp_user_config)
    assert zazu.config.complete_param(None, [], '') == ['scm_host.gh.type', 'scm_host.gh.user']
    assert zazu.config.complete_param(None, ['--add'], '') == []
