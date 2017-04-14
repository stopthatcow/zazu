# -*- coding: utf-8 -*-

import zazu.plugins.jira_issue_tracker

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_jira_issue_tracker():
    jira = zazu.plugins.jira_issue_tracker.JiraIssueTracker('jira', 'project', ['NA'])
