# -*- coding: utf-8 -*-
import click
import pytest
import zazu.dev.commands

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


def test_issue_descriptor():
    uut = zazu.dev.commands.IssueDescriptor('feature', '3')
    assert uut.get_branch_name() == 'feature/3'
    uut = zazu.dev.commands.IssueDescriptor('feature', '3', 'a description')
    assert uut.get_branch_name() == 'feature/3_a_description'
    assert uut.readable_description() == 'A description'


def test_verify_ticket_exists(mocker):
    issue_tracker_mock = mocker.Mock()
    issue_tracker_mock.issue = mocker.Mock(side_effect=zazu.issue_tracker.IssueTrackerError("No ticket found"))
    with pytest.raises(click.ClickException) as e:
        zazu.dev.commands.verify_ticket_exists(issue_tracker_mock, '1')
    assert str(e.value) == 'no ticket for id "1"'
    issue_tracker_mock.issue = mocker.Mock()
    zazu.dev.commands.verify_ticket_exists(issue_tracker_mock, '1')


def test_offer_to_stash_changes(mocker):
    mock_repo = mocker.Mock()
    mock_repo.index = mocker.Mock()
    mock_repo.index.diff = mocker.Mock(return_value=' ')
    mock_repo.git = mocker.Mock()
    mock_repo.git.status = mocker.Mock(return_value=' ')
    mock_repo.git.stash = mocker.Mock()
    mocker.patch('click.confirm', return_value=True)
    zazu.dev.commands.offer_to_stash_changes(mock_repo)
    assert click.confirm.call_count == 1
    click.confirm.assert_called_once_with('Local changes detected, stash first?', default=True)


def test_make_issue_descriptor_bad_type():
    with pytest.raises(click.ClickException) as e:
        zazu.dev.commands.make_issue_descriptor('bad/1')
    assert str(e.value).startswith('Branch type specifier must be one of ')


def test_make_issue_descriptor_github_style():
    with pytest.raises(click.ClickException) as e:
        zazu.dev.commands.make_issue_descriptor('bad/1')
    assert str(e.value).startswith('Branch type specifier must be one of ')
    branch_name ='feature/1_description'
    uut = zazu.dev.commands.make_issue_descriptor(branch_name)
    assert uut.get_branch_name() == branch_name
    assert uut.type == 'feature'
    assert uut.id == '1'
    assert uut.description == 'description'


def test_make_issue_descriptor_jira_style():
    branch_name ='feature/ZZ-1_description'
    uut = zazu.dev.commands.make_issue_descriptor(branch_name)
    assert uut.get_branch_name() == branch_name
    assert uut.type == 'feature'
    assert uut.id == 'ZZ-1'
    assert uut.description == 'description'


def test_make_ticket(mocker):
    mock_issue_tracker = mocker.Mock('zazu.issue_tracker.IssueTracker', autospec=True)
    mocker.patch('zazu.util.prompt', side_effect=['title', 'description'])
    mock_issue_tracker.connect = mocker.Mock()
    mock_issue_tracker.create_issue = mocker.Mock()
    mock_issue_tracker.default_project = mocker.Mock(return_value='project')
    mock_issue_tracker.issue_types = mocker.Mock(return_value=['type'])
    mock_issue_tracker.issue_components = mocker.Mock(return_value=['component'])
    zazu.dev.commands.make_ticket(mock_issue_tracker)
    mock_issue_tracker.create_issue.assert_called_once_with(project='project',
                                                            issue_type='type',
                                                            summary='title',
                                                            description='description',
                                                            component='component')