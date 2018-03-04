# -*- coding: utf-8 -*-
import click
import os
import pytest
import ruamel.yaml as yaml
import zazu.config

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@pytest.fixture()
def repo_with_teamcity(git_repo):
    root = git_repo.working_tree_dir
    teamcity_config = {
        'ci': {
            'type': 'TeamCity',
            'url': 'http://teamcity.zazu.technology:8111/'
        }
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        yaml.dump(teamcity_config, file)
    return git_repo


@pytest.fixture()
def repo_with_invalid_ci(git_repo):
    root = git_repo.working_tree_dir
    teamcity_config = {
        'ci': {
            'type': 'foobar',
        }
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        yaml.dump(teamcity_config, file)
    return git_repo


@pytest.fixture()
def repo_with_jira(git_repo):
    root = git_repo.working_tree_dir
    jira_config = {
        'issueTracker': {
            'type': 'Jira',
            'url': 'https://zazu.atlassian.net/',
            'project': 'TEST',
            'component': 'Zazu'
        }
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        yaml.dump(jira_config, file)
    return git_repo


def test_teamcity_config(repo_with_teamcity):
    cfg = zazu.config.Config(repo_with_teamcity.working_tree_dir)
    tc = cfg.build_server()
    assert tc is not None
    assert tc.type() == 'TeamCity'


def test_invalid_ci(repo_with_invalid_ci):
    cfg = zazu.config.Config(repo_with_invalid_ci.working_tree_dir)
    with pytest.raises(click.ClickException):
        cfg.build_server()


def test_jira_config(repo_with_jira):
    cfg = zazu.config.Config(repo_with_jira.working_tree_dir)
    tracker = cfg.issue_tracker()
    assert tracker is not None
    assert tracker.type() == 'Jira'


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
    uut._project_config = {'style': {'foo': {}}}
    with pytest.raises(click.ClickException):
        uut.stylers()


def test_unknown_scm_host():
    uut = zazu.config.Config('')
    uut._user_config = {'scmHost': {'gh': {'type': ''}}}
    with pytest.raises(click.ClickException):
        uut.scm_hosts()


def test_no_type_scm_host():
    uut = zazu.config.Config('')
    uut._user_config = {'scmHost': {'gh': {}}}
    with pytest.raises(click.ClickException):
        uut.scm_hosts()


def test_no_scm_host():
    uut = zazu.config.Config('')
    uut._user_config = {}
    with pytest.raises(click.ClickException):
        uut.scm_hosts()


def test_github_scm_host():
    uut = zazu.config.Config('')
    uut._user_config = {'scmHost': {'gh': {'type': 'github', 'user': 'user'}}}
    assert uut.scm_hosts()
    assert uut.scm_hosts()['gh']


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
    uut._project_config = {'codeReviewer': {'type': 'github'}}
    assert uut.code_reviewer()
