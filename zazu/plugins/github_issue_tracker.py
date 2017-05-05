# -*- coding: utf-8 -*-
"""The goal of the GITHUB issue tracker is to expose a simple interface that will allow us to collect ticket information
 pertaining to the current branch based on ticket ID. Additionally we can integrate with GITHUB to create new tickets
 for bug fixes and features"""
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

ZAZU_IMAGE_URL = 'http://vignette1.wikia.nocookie.net/disney/images/c/ca/Zazu01cf.png'
ZAZU_REPO_URL = 'https://github.com/stopthatcow/zazu'
GITHUB_CREATED_BY_ZAZU = '----\n!{}|width=20! Created by [Zazu|{}]'.format(ZAZU_IMAGE_URL, ZAZU_REPO_URL)


class GithubIssueTracker(zazu.issue_tracker.IssueTracker):
    """Implements zazu issue tracker interface for GITHUB"""

    def __init__(self, org, repo):
        self._base_url = 'https://github.com/{}/{}'.format(org, repo)
        self._org = org
        self._repo = repo
        self._github_handle = None

    def connect(self):
        """Get handle to ensure that github credentials are in place"""
        self.github_handle()

    def github_handle(self):
        if self._github_handle is None:
            self._github_handle = zazu.github_helper.make_gh()
        return self._github_handle

    def github_repo(self):
        return self.github_handle().get_user(self._org).get_repo(self._repo)

    def browse_url(self, issue_id):
        return '{}/issues/{}'.format(self._base_url, issue_id)

    def issue(self, issue_id):
        try:
            return GitHubIssueAdaptor(self.github_repo().get_issue(int(issue_id)))
        except github.GithubException as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))
        except ValueError:
            raise zazu.issue_tracker.IssueTrackerError('Invalid issue id {}'.format(issue_id))

    def create_issue(self, project, issue_type, summary, description, component):
        try:
            return GitHubIssueAdaptor(self.github_repo().create_issue(title=summary, body=description))
        except github.GithubException as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def assign_issue(self, issue, assignee):
        try:
            issue.edit(assignee=assignee)
        except github.GithubException as e:
            raise zazu.issue_tracker.IssueTrackerError(str(e))

    def default_project(self):
        return ''

    def issue_types(self):
        return ['Issue']

    def issue_components(self):
        return ['']

    @staticmethod
    def from_config(config):
        """Makes a GithubIssueTracker from a config"""
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
        return GithubIssueTracker(owner, repo_name)

    @staticmethod
    def type():
        return 'github'


class GitHubIssueAdaptor(zazu.issue_tracker.Issue):

    def __init__(self, github_issue):
        self._github_issue = github_issue

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

    def __str__(self):
        return str(self._github_issue.number)
