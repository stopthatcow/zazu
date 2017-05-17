# -*- coding: utf-8 -*-

import zazu.plugins.github_issue_tracker

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


def test_github_issue_tracker():
    result = zazu.plugins.github_issue_tracker.GithubIssueTracker.from_config({'owner': 'foo',
                                                                               'repo': 'bar'})
    assert result._owner == 'foo'
    assert result._repo == 'bar'
