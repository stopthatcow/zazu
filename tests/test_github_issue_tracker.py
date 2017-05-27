# -*- coding: utf-8 -*-
import conftest
import pytest
import zazu.plugins.github_issue_tracker

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@pytest.fixture
def tracker_mock():
    return zazu.plugins.github_issue_tracker.GitHubIssueTracker('stopthatcow', 'zazu')


def test_github_issue_adaptor(tracker_mock):
    mock_issue_dict = {
        'number': 1,
        'title': 'name',
        'state': 'closed',
        'body': 'description',
        'assignees': [{'login': 'assignee'}]
    }
    mock_issue = conftest.dict_to_obj(mock_issue_dict)

    uut = zazu.plugins.github_issue_tracker.GitHubIssueAdaptor(mock_issue, tracker_mock)
    assert uut.name == 'name'
    assert uut.status == 'closed'
    assert uut.description == 'description'
    assert uut.reporter == 'unknown'
    assert uut.assignee == 'assignee'
    assert uut.closed
    assert uut.type == 'issue'
    assert uut.browse_url == 'https://github.com/stopthatcow/zazu/issues/1'
    assert uut.id == '1'
    assert str(uut) == uut.id
