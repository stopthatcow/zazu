# -*- coding: utf-8 -*-
import zazu.imports

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"

zazu.imports.lazy_import(locals(), [
    'zazu.plugins.jira_issue_tracker',
    'zazu.plugins.github_issue_tracker',
    'ruamel.yaml'
])


def test_lazy_imports():
    assert 'github_issue_tracker' in zazu.plugins.__dict__
    assert 'jira_issue_tracker' in zazu.plugins.__dict__
    assert zazu.plugins.jira_issue_tracker.IssueTracker
    assert zazu.plugins.github_issue_tracker.IssueTracker
    assert ruamel.yaml.YAMLError
