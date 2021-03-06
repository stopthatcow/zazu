# -*- coding: utf-8 -*-
"""Classes that adapt GitHub for use as a zazu IssueTracker."""
import zazu.imports
zazu.imports.lazy_import(locals(), [
    'git',
    'github',
    'os',
    'zazu.github_helper',
    'zazu.issue_tracker',
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


class IssueTracker(zazu.issue_tracker.IssueTracker):
    """Implements zazu issue tracker interface for GitHub."""

    def __init__(self, owner, repo, url=None):
        """Create a GitHubIssueTracker.

        Args:
            owner (str): the github repo owner's username or organization name.
            repo (str): the github repo name.

        """
        self._owner = owner
        self._repo = repo
        self._url = url
        self._github_handle = None
        self._user = None

    def connect(self):
        """Get handle to ensure that github credentials are in place."""
        self._github()

    def _github(self):
        if self._github_handle is None:
            self._github_handle = zazu.github_helper.make_gh(self._url)
        return self._github_handle

    def _github_repo(self):
        return self._github().get_user(self._owner).get_repo(self._repo)

    def user(self):
        """Get username of authenticated user."""
        if self._user is None:
            self._user = self._github().get_user().login
        return self._user

    def issue(self, issue_id):
        """Get an issue by id."""
        self.validate_id_format(issue_id)
        try:
            return GitHubIssueAdaptor(self._github_repo().get_issue(int(issue_id)))
        except github.GithubException as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def create_issue(self, project, issue_type, summary, description, component):
        """Create a new issue on github.

        Args:
            project (str): meaningless for GitHub.
            issue_type (str): meaningless for GitHub.
            summary (str): a summary of the issue.
            description (str): a detailed description of the issue.
            component (str): meaningless for GitHub.

        """
        try:
            return GitHubIssueAdaptor(self._github_repo().create_issue(title=summary, body=description, assignee=self.user()))
        except github.GithubException as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def issues(self):
        """Get all issues."""
        try:
            return [GitHubIssueAdaptor(i) for i in self._github_repo().get_issues()]
        except github.GithubException as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def assign_issue(self, issue, user):
        """Assign an issue to a user."""
        issue._github_issue.edit(assignee=user)

    def default_project(self):
        """Meaningless for GitHub."""
        return ''

    def issue_types(self):
        """There is only has 1 issue type on GitHub."""
        return ['issue']

    def issue_components(self):
        """Meaningless for GitHub."""
        return []

    def validate_id_format(self, id):
        """Validate that an id is the proper format for GitHub.

        Args:
            id (str): the id to check.

        Raises:
            zazu.issue_tracker.IssueTrackerError: if the id is not valid.

        Returns:
            normalized id string

        """
        if not id.isdigit():
            raise zazu.issue_tracker.IssueTrackerError('issue id "{}" is not numeric'.format(id))
        return id

    @staticmethod
    def from_config(config):
        """Make a GitHubIssueTracker from a config."""
        # Get URL from current git repo:
        owner = config.get('owner', None)
        repo_name = config.get('repo', None)
        github_url = config.get('url', None)
        if owner is None or repo_name is None:
            repo = git.Repo(zazu.git_helper.get_repo_root(os.getcwd()))
            try:
                remote = repo.remotes.origin
            except AttributeError:
                raise zazu.issue_tracker.IssueTrackerError('No "origin" remote specified for this repo')
            owner, repo_name = zazu.github_helper.parse_github_url(remote.url)
        return IssueTracker(owner, repo_name, github_url)

    @staticmethod
    def type():
        """Return the name of this IssueTracker type."""
        return 'github'


class GitHubIssueAdaptor(zazu.issue_tracker.Issue):
    """Wraps a returned issue from PyGithub and adapts it to the zazu.issue_tracker.Issue interface."""

    def __init__(self, github_issue):
        """Create a zazu Issue interface by wrapping a PyGithub Issue.

        Args:
            github_issue: PyGithub issue handle.

        """
        self._github_issue = github_issue

    @property
    def name(self):
        """Get the name of the issue."""
        return self._github_issue.title

    @property
    def status(self):
        """Get the status string of the issue."""
        return self._github_issue.state

    @property
    def description(self):
        """Get the description of the issue."""
        return self._github_issue.body

    @property
    def type(self):
        """Get the string type of the issue."""
        return 'issue'

    @property
    def assignee(self):
        """Get the string assignee of the issue."""
        return self._github_issue.assignees[0].login

    @property
    def closed(self):
        """Return True if the issue is closed."""
        return str(self._github_issue.state) == 'closed'

    @property
    def browse_url(self):
        """Get the url to open to display the issue."""
        return self._github_issue.html_url

    @property
    def id(self):
        """Get the string id of the issue."""
        return str(self._github_issue.number)

    def __lt__(self, other):
        """Allow issues to be sorted as numbers."""
        if isinstance(other, GitHubIssueAdaptor):
            return self._github_issue.number < other._github_issue.number
        return self._github_issue.number < int(str(other))
