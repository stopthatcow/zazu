# -*- coding: utf-8 -*-
"""The goal of the JIRA helper is to expose a simple interface that will allow us to collect ticket information pertaining to
the current branch based on ticket ID. Additionally we can integrate with JIRA to create new tickets for bug fixes and features"""

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

from jira import JIRA
import credential_helper

# TODO: config this
jira_base_url = 'https://lily-robotics.atlassian.net'


def make_jira():
    username, password = credential_helper.get_user_pass_credentials('Jira')
    jira = JIRA(jira_base_url, basic_auth=(username, password), options={'check_update': False})
    return jira


def get_browse_url(issue_id):
    return '{}/browse/{}'.format(jira_base_url, issue_id)


# Some ideas for APIs
# list work assigned to me in this sprint
# create new ticket and then start a feature branch based on the created ID
# update ticket progress (transition states)
