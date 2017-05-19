# -*- coding: utf-8 -*-
import conftest
import zazu.plugins.github_code_reviewer

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


def test_github_issue_tracker():
    result = zazu.plugins.github_code_reviewer.GitHubCodeReviewer.from_config({'owner': 'foo',
                                                                               'repo': 'bar'})
    assert result._base_url == 'https://github.com/foo/bar'
    assert result._owner == 'foo'
    assert result._repo == 'bar'


def test_github_code_review_adaptor():
    mock_issue_dict = {
        'number': 3,
        'title': 'name',
        'state': 'closed',
        'resolution': {
            'name': 'Done'
        },
        'body': 'description',
        'assignee': {
            'login': 'assignee'
        },
        'head': {
            'ref': 'foo:head'
        },
        'base': {
            'ref': 'base'
        },
        'html_url': 'browse_url',
        'merged': False
    }
    mock_issue = conftest.dict_to_obj(mock_issue_dict)

    uut = zazu.plugins.github_code_reviewer.GitHubCodeReview(mock_issue)
    assert uut.name == 'name'
    assert uut.status == 'closed'
    assert uut.description == 'description'
    assert uut.assignee == 'assignee'
    assert uut.head == 'foo:head'
    assert uut.base == 'base'
    assert uut.browse_url == 'browse_url'
    assert not uut.merged
    assert str(uut) == '#3 (closed, unmerged) foo:head -> base'
