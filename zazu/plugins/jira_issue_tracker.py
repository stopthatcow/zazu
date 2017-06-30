# -*- coding: utf-8 -*-
"""The goal of the JIRA issue tracker is to expose a simple interface that will allow us to collect ticket information
 pertaining to the current branch based on ticket ID. Additionally we can integrate with JIRA to create new tickets
 for bug fixes and features"""
import zazu.credential_helper
import zazu.issue_tracker
import zazu.util
zazu.util.lazy_import(locals(), [
    'jira',
    're'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"

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

    def jira_handle(self):
        if self._jira_handle is None:
            username, password = zazu.credential_helper.get_user_pass_credentials('Jira')
            self._jira_handle = jira.JIRA(self._base_url,
                                          basic_auth=(username, password),
                                          options={'check_update': False}, max_retries=0)
        return self._jira_handle

    def browse_url(self, id):
        self.validate_id_format(id)
        return '{}/browse/{}'.format(self._base_url, id)

    def issue(self, id):
        self.validate_id_format(id)
        try:
            ret = self.jira_handle().issue(id)
            # Only show description up to the separator
            if ret.fields.description is None:
                ret.fields.description = ''
            ret.fields.description = ret.fields.description.split('\n\n----', 1)[0]
        except jira.exceptions.JIRAError as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))
        return JiraIssueAdaptor(ret, self)

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
            issue = self.jira_handle().create_issue(issue_dict)
            self.jira_handle().assign_issue(issue, issue.fields.reporter.name)
            return JiraIssueAdaptor(issue, self)
        except jira.exceptions.JIRAError as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def default_project(self):
        return self._default_project

    def issue_types(self):
        return ['Task', 'Bug', 'Story']

    def issue_components(self):
        return self._components

    @staticmethod
    def validate_id_format(id):
        if not re.match('[A-Z]+-[0-9]+$', id):
            raise zazu.issue_tracker.IssueTrackerError('issue id "{}" is not of the form PROJ-#'.format(id))

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


class JiraIssueAdaptor(zazu.issue_tracker.Issue):
    """Wraps a issue returned from the jiri api and adapts it to the zazu.issue_tracker.Issue interface"""

    def __init__(self, jira_issue, tracker_handle):
        self._jira_issue = jira_issue
        self._tracker = tracker_handle

    @property
    def name(self):
        return self._jira_issue.fields.summary

    @property
    def status(self):
        return self._jira_issue.fields.status.name

    @property
    def description(self):
        return self._jira_issue.fields.description

    @property
    def type(self):
        return self._jira_issue.fields.issuetype.name

    @property
    def reporter(self):
        return self._jira_issue.fields.reporter.name

    @property
    def assignee(self):
        return self._jira_issue.fields.assignee.name

    @property
    def closed(self):
        return self._jira_issue.fields.resolution.name != 'Unresolved'

    @property
    def browse_url(self):
        return self._tracker.browse_url(self.id)

    @property
    def id(self):
        return self._jira_issue.key

    def __str__(self):
        return self.id
