# -*- coding: utf-8 -*-
import conftest
import pytest
import zazu.plugins.jira_issue_tracker

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class MockJira(object):
    pass


def test_jira_issue_tracker(mocker):
    mocker.patch('zazu.credential_helper.get_user_pass_credentials', return_value=('user', 'pass'))
    mocker.patch('jira.JIRA', return_value=MockJira())
    uut = zazu.plugins.jira_issue_tracker.JiraIssueTracker.from_config({'url': 'https://jira',
                                                                        'project': 'ZZ',
                                                                        'component': 'comp'})
    uut.connect()
    assert uut.default_project() == 'ZZ'
    assert uut.issue_components() == ['comp']
    assert uut.issue_types() == ['Task', 'Bug', 'Story']


def test_from_config():
    with pytest.raises(zazu.ZazuException):
        zazu.plugins.jira_issue_tracker.JiraIssueTracker.from_config({'url': 'https://jira'})
    with pytest.raises(zazu.ZazuException):
        zazu.plugins.jira_issue_tracker.JiraIssueTracker.from_config({'project': 'ZZ'})


def test_jira_validate_id_format():
    uut = tracker_mock()
    uut.validate_id_format('LC-10')
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('lc-10')
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('LC1-10')
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('LC-10a')
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('10')
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('10a')


@pytest.fixture
def tracker_mock():
    return zazu.plugins.jira_issue_tracker.JiraIssueTracker('https://jira', 'project', ['NA'])


def test_jira_issue_adaptor(tracker_mock):
    mock_issue_dict = {
        'fields': {
            'summary': 'name',
            'status': {
                'name': 'Closed'
            },
            'resolution': {
                'name': 'Done'
            },
            'description': 'description',
            'issuetype': {
                'name': 'type'
            },
            'reporter': {
                'name': 'reporter'
            },
            'assignee': {
                'name': 'assignee'
            },
        },
        'key': 'ZZ-1'
    }
    mock_issue = conftest.dict_to_obj(mock_issue_dict)

    uut = zazu.plugins.jira_issue_tracker.JiraIssueAdaptor(mock_issue, tracker_mock)
    assert uut.name == 'name'
    assert uut.status == 'Closed'
    assert uut.description == 'description'
    assert uut.reporter == 'reporter'
    assert uut.assignee == 'assignee'
    assert uut.closed
    assert uut.type == 'type'
    assert uut.browse_url == 'https://jira/browse/ZZ-1'
    assert uut.id == 'ZZ-1'
    assert str(uut) == uut.id
