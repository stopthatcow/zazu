# -*- coding: utf-8 -*-
import conftest
import pytest
import zazu.plugins.jira_issue_tracker

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


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
