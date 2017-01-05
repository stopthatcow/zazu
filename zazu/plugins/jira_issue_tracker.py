# -*- coding: utf-8 -*-
"""The goal of the JIRA issue tracker is to expose a simple interface that will allow us to collect ticket information
 pertaining to the current branch based on ticket ID. Additionally we can integrate with JIRA to create new tickets
 for bug fixes and features"""

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"

import jira
import zazu.credential_helper
import zazu.issue_tracker


ZAZU_IMAGE_URL = 'http://vignette1.wikia.nocookie.net/disney/images/c/ca/Zazu01cf.png'
ZAZU_REPO_URL = 'https://github.com/stopthatcow/zazu'
JIRA_CREATED_BY_ZAZU = '----\n!{}|width=20! Created by [Zazu|{}]'.format(ZAZU_IMAGE_URL, ZAZU_REPO_URL)


class JiraIssueTracker(zazu.issue_tracker.IssueTracker):
    """Implements zazu issue tracker interface for JIRA"""

    def __init__(self, base_url, default_project, components):
        self._base_url = base_url
        self._default_project = default_project
        self._components = components
        self._jira_handle = None

    def connect(self):
        """Get handle to ensure that JIRA credentials are in place"""
        self.jira_handle()

    @staticmethod
    def closed(issue):
        return str(issue.fields.status) == 'Closed'

    @staticmethod
    def resolved(issue):
        return str(issue.fields.status) == 'Resolved'

    def jira_handle(self):
        if self._jira_handle is None:
            username, password = zazu.credential_helper.get_user_pass_credentials('Jira')
            self._jira_handle = jira.JIRA(self._base_url,
                                          basic_auth=(username, password),
                                          options={'check_update': False}, max_retries=0)
        return self._jira_handle

    def browse_url(self, issue_id):
        return '{}/browse/{}'.format(self._base_url, issue_id)

    def issue(self, issue_id):
        try:
            import re
            ret = self.jira_handle().issue(issue_id)
            # Only show description up to the separator
            ret.fields.description = ret.fields.description.split('\n\n----')[0]
        except jira.exceptions.JIRAError as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))
        return ret

    def create_issue(self, project, issue_type, summary, description, component):
        try:
            issue_dict = {
                'project': {'key': project},
                'issuetype': {'name': issue_type},
                'summary': summary,
                'description': '{}\n\n{}'.format(description, JIRA_CREATED_BY_ZAZU)
            }
            if component is not None:
                issue_dict['components'] = [{'name': component}]
            return self.jira_handle().create_issue(issue_dict)
        except jira.exceptions.JIRAError as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def assign_issue(self, issue, assignee):
        try:
            self.jira_handle().assign_issue(issue, assignee)
        except jira.exceptions.JIRAError as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def default_project(self):
        return self._default_project

    def issue_types(self):
        return ['Task', 'Bug', 'Story']

    def issue_components(self):
        return self._components

    @staticmethod
    def from_config(config):
        """Makes a JiraIssueTracker from a config"""
        try:
            url = config['url']
        except KeyError:
            raise zazu.ZazuException('Jira config requires a "url" field')
        try:
            project = config['project']
        except KeyError:
            raise zazu.ZazuException('Jira config requires a "project" field')
        components = config.get('component', None)
        if not isinstance(components, list):
            components = [components]
        return JiraIssueTracker(url, project, components)

    @staticmethod
    def type():
        return 'Jira'

# Some ideas for APIs
# list work assigned to me in this sprint
# update ticket progress (transition states)
