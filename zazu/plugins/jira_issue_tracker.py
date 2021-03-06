# -*- coding: utf-8 -*-
"""Classes that adapt JIRA for use as a zazu IssueTracker."""
import zazu.imports
zazu.imports.lazy_import(locals(), [
    'click',
    'jira',
    're',
    'zazu.credential_helper',
    'zazu.issue_tracker',
    'zazu.util',
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'

ZAZU_IMAGE_URL = 'http://vignette1.wikia.nocookie.net/disney/images/c/ca/Zazu01cf.png'
ZAZU_REPO_URL = 'https://github.com/stopthatcow/zazu'
JIRA_CREATED_BY_ZAZU = '----\nCreated by [Zazu|{}].'.format(ZAZU_REPO_URL)


class IssueTracker(zazu.issue_tracker.IssueTracker):
    """Implements zazu issue tracker interface for JIRA."""

    def __init__(self, base_url, default_project, components):
        """Create a JiraIssueTracker.

        Args:
            base_url (str): base URL for the JIRA instance.
            default_project (str): project that new issues will be created in by default.
            components (list of str): list of components that new issues can be associated with.

        """
        self._base_url = base_url
        self._user = None
        self._default_project = default_project
        self._components = components
        self._jira_handle = None

    def connect(self):
        """Get handle to ensure that JIRA credentials are in place."""
        self._jira()

    def _jira(self):
        if self._jira_handle is None:
            use_saved = True
            while True:
                user, password = zazu.credential_helper.get_user_pass_credentials(self._base_url, use_saved=use_saved)
                try:
                    self._jira_handle = jira.JIRA(self._base_url,
                                                  basic_auth=(user, password),
                                                  options={'check_update': False}, max_retries=0)
                    break
                except jira.JIRAError as e:
                    if e.status_code == 401:
                        click.echo('{} rejected password for user {}!'.format(self._base_url, user))
                        use_saved = False
                    else:
                        raise zazu.issue_tracker.IssueTrackerError(str(e))
        return self._jira_handle

    def browse_url(self, id):
        """Get the url to open to display the issue."""
        normalized_id = self.validate_id_format(id)
        return '{}/browse/{}'.format(self._base_url, normalized_id)

    def user(self):
        """Get username of authenticated user."""
        if self._user is None:
            self._user = self._jira().current_user()
        return self._user

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
            # TODO(stopthatcow): Re-enable once assign_issue() works again due to GDPR changes.
            # self._jira().assign_issue(issue, issue.fields.reporter.name)
            return JiraIssueAdaptor(issue, self)
        except jira.exceptions.JIRAError as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def issues(self):
        """List all open issues."""
        issues = self._jira().search_issues('assignee={} AND resolution="Unresolved"'.format(self.user()),
                                            fields='key, summary, description')
        return [JiraIssueAdaptor(i, self) for i in issues]

    def assign_issue(self, issue, user):
        """Assign an issue to a user."""
        self._jira().assign_issue(issue._jira_issue, user)

    def default_project(self):
        """JIRA project associated with this tracker."""
        return self._default_project

    def issue_types(self):
        """Issue types that can be created by this tracker."""
        return ['Task', 'Bug', 'Story']

    def issue_components(self):
        """Get components that are associated with this tracker."""
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
        return IssueTracker(url, project, components)

    @staticmethod
    def type():
        """Return the name of this IssueTracker type."""
        return 'jira'


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

    def parse_key(self):
        """Parse key into project prefix and issue number."""
        components = self._jira_issue.key.split('-')
        return components[0], int(components[1])

    def __lt__(self, other):
        """Allow issues to be sorted in natural order.

        First by project prefix, then by ID.

        """
        if isinstance(other, JiraIssueAdaptor):
            return self.parse_key() < other.parse_key()
        return str(self) < str(other)
