# -*- coding: utf-8 -*-
"""Clasess that adapt JIRA for use as a zazu IssueTracker."""
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
    """Implements zazu issue tracker interface for JIRA."""

    def __init__(self, base_url, default_project, components):
        """Create a JiraIssueTracker.

        Args:
            base_url (str): base URL for the JIRA instance.
            default_project (str): project that new issues will be created in by default.
            components (list of str): list of components that new issues can be associated with.
        """
        self._base_url = base_url
        self._default_project = default_project
        self._components = components
        self._jira_handle = None

    def connect(self):
        """Get handle to ensure that JIRA credentials are in place."""
        self._jira()

    def _jira(self):
        if self._jira_handle is None:
            self._username, password = zazu.credential_helper.get_user_pass_credentials('Jira')
            self._jira_handle = jira.JIRA(self._base_url,
                                          basic_auth=(self._username, password),
                                          options={'check_update': False}, max_retries=0)
        return self._jira_handle

    def browse_url(self, id):
        """Get the url to open to display the issue."""
        normalized_id = self.validate_id_format(id)
        return '{}/browse/{}'.format(self._base_url, normalized_id)

    def issue(self, id):
        """Get an issue by id."""
        normalized_id = self.validate_id_format(id)
        try:
            ret = self._jira().issue(normalized_id)
            # Only show description up to the separator
            if ret.fields.description is None:
                ret.fields.description = ''
            ret.fields.description = ret.fields.description.split('\n\n----', 1)[0]
        except jira.exceptions.JIRAError as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))
        return JiraIssueAdaptor(ret, self)

    def create_issue(self, project, issue_type, summary, description, component):
        """Create a new issue on JIRA.

        Args:
            project (str): the JIRA project short string to create the issue in.
            issue_type (str): the JIRA issue type to create.
            summary (str): a summary of the issue.
            description (str): a detailed description of the issue.
            component (str): the JIRA component to associate with the issue.
        """
        try:
            issue_dict = {
                'project': {'key': project},
                'issuetype': {'name': issue_type},
                'summary': summary,
                'description': '{}\n\n{}'.format(description, JIRA_CREATED_BY_ZAZU)
            }
            if component is not None:
                issue_dict['components'] = [{'name': component}]
            issue = self._jira().create_issue(issue_dict)
            self._jira().assign_issue(issue, issue.fields.reporter.key)
            return JiraIssueAdaptor(issue, self)
        except jira.exceptions.JIRAError as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def assign_issue_to_me(self, issue):
        """Assigns an issue to username of the client"""
        self._jira().assign_issue(issue, self._jira().current_user())

    def default_project(self):
        """JIRA project associated with this tracker."""
        return self._default_project

    def issue_types(self):
        """Issue types that can be created by this tracker."""
        return ['Task', 'Bug', 'Story']

    def issue_components(self):
        """Components that are associated with this tracker."""
        return self._components

    def validate_id_format(self, id):
        """Validate that an id is the proper format for Jira.

        Args:
            id (str): the id to check.

        Raises:
            zazu.issue_tracker.IssueTrackerError: if the id is not valid.

        Returns:
            normalized id string
        """
        components = id.split('-', 1)
        number = components.pop()
        project = components.pop().upper() if components else self._default_project
        if project != self._default_project:
            raise zazu.issue_tracker.IssueTrackerError('project "{}" is not "{}"'.format(project, self._default_project))

        if not re.match('[0-9]+$', number):
            raise zazu.issue_tracker.IssueTrackerError('issue number is not numeric')
        return '{}-{}'.format(project, number)

    @staticmethod
    def from_config(config):
        """Make a JiraIssueTracker from a config."""
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
        """Return the name of this IssueTracker type."""
        return 'Jira'


class JiraIssueAdaptor(zazu.issue_tracker.Issue):
    """Wraps a issue returned from the jiri api and adapts it to the zazu.issue_tracker.Issue interface."""

    def __init__(self, jira_issue, tracker_handle):
        """Create a JiraIssueAdaptor by wrapping a jira Issue object.

        Args:
            jira_issue: Jira issue handle.
            tracker_handle: The tracker associated with this issue.
        """
        self._jira_issue = jira_issue
        self._tracker = tracker_handle

    @property
    def name(self):
        """Get the name of the issue."""
        return self._jira_issue.fields.summary

    @property
    def status(self):
        """Get the status string of the issue."""
        return self._jira_issue.fields.status.name

    @property
    def description(self):
        """Get the description of the issue."""
        return self._jira_issue.fields.description

    @property
    def type(self):
        """Get the string type of the issue."""
        return self._jira_issue.fields.issuetype.name

    @property
    def assignee(self):
        """Get the string assignee of the issue."""
        return self._jira_issue.fields.assignee.name

    @property
    def closed(self):
        """Return True if the issue is closed."""
        return self._jira_issue.fields.resolution.name != 'Unresolved'

    @property
    def browse_url(self):
        """Get the url to open to display the issue."""
        return self._tracker.browse_url(self.id)

    @property
    def id(self):
        """Get the string id of the issue."""
        return self._jira_issue.key
