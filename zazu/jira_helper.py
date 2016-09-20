# -*- coding: utf-8 -*-
"""The goal of the JIRA helper is to expose a simple interface that will allow us to collect ticket information pertaining to
the current branch based on ticket ID. Additionally we can integrate with JIRA to create new tickets for bug fixes and features"""

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

import jira
import zazu.credential_helper


def make_jira(base_url):
    username, password = zazu.credential_helper.get_user_pass_credentials('Jira')
    ret = jira.JIRA(base_url, basic_auth=(username, password), options={'check_update': False}, max_retries=0)
    return ret


def get_browse_url(base_url, issue_id):
    return '{}/browse/{}'.format(jira_base_url, issue_id)


def get_issue(jira_handle, issue_id):
    ret = None
    try:
        ret = jira_handle.issue(issue_id)
    except jira.exceptions.JIRAError:
        pass
    return ret

# Some ideas for APIs
# list work assigned to me in this sprint
# update ticket progress (transition states)
