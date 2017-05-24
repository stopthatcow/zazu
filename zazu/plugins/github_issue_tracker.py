# -*- coding: utf-8 -*-
"""The GitHubIssueTracker implements the zazu.issue_tracker.IssueTracker plugin interface for managing tickets on github"""
import zazu.github_helper
import zazu.issue_tracker
import zazu.util
zazu.util.lazy_import(locals(), [
    'git',
    'github',
    'os'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class GitHubIssueTracker(zazu.issue_tracker.IssueTracker):
    """Implements zazu issue tracker interface for GitHub"""

    def __init__(self, owner, repo):
        self._base_url = 'https://github.com/{}/{}'.format(owner, repo)
        self._owner = owner
        self._repo = repo
        self._github = None

    def connect(self):
        """Get handle to ensure that github credentials are in place"""
        self._github_handle()

    def _github_handle(self):
        if self._github is None:
            self._github = zazu.github_helper.make_gh()
        return self._github

    def _github_repo(self):
        return self._github_handle().get_user(self._owner).get_repo(self._repo)

    def browse_url(self, issue_id):
        self.validate_id_format(issue_id)
        return '{}/issues/{}'.format(self._base_url, issue_id)

    def issue(self, issue_id):
        self.validate_id_format(issue_id)
        try:
            return GitHubIssueAdaptor(self._github_repo().get_issue(int(issue_id)), self)
        except github.GithubException as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def create_issue(self, project, issue_type, summary, description, component):
        try:
            return GitHubIssueAdaptor(self._github_repo().create_issue(title=summary, body=description), self)
        except github.GithubException as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def default_project(self):
        return ''

    def issue_types(self):
        return ['issue']

    def issue_components(self):
        return []

    @staticmethod
    def validate_id_format(id):
        if not id.isdigit():
            raise zazu.issue_tracker.IssueTrackerError('issue id "{}" is not numeric'.format(id))

    @staticmethod
    def from_config(config):
        """Makes a GitHubIssueTracker from a config"""
        # Get URL from current git repo:
        owner = config.get('owner', None)
        repo_name = config.get('repo', None)
        if owner is None or repo_name is None:
            repo = git.Repo(zazu.git_helper.get_repo_root(os.getcwd()))
            try:
                remote = repo.remotes.origin
            except AttributeError:
                raise zazu.issue_tracker.IssueTrackerError('No "origin" remote specified for this repo')
            owner, repo_name = zazu.github_helper.parse_github_url(remote.url)
        return GitHubIssueTracker(owner, repo_name)

    @staticmethod
    def type():
        return 'github'


class GitHubIssueAdaptor(zazu.issue_tracker.Issue):
    """Wraps a returned issue from pygithub and adapts it to the zazu.issue_tracker.Issue interface"""

    def __init__(self, github_issue, tracker_handle):
        self._github_issue = github_issue
        self._tracker = tracker_handle

    @property
    def name(self):
        return self._github_issue.title

    @property
    def status(self):
        return self._github_issue.state

    @property
    def description(self):
        return self._github_issue.body

    @property
    def type(self):
        return 'issue'

    @property
    def reporter(self):
        return 'unknown'

    @property
    def assignee(self):
        return self._github_issue.assignees[0].login

    @property
    def closed(self):
        return str(self._github_issue.state) == 'closed'

    @property
    def browse_url(self):
        return self._tracker.browse_url(self.id)

    @property
    def id(self):
        return str(self._github_issue.number)

    def __str__(self):
        return self.id
