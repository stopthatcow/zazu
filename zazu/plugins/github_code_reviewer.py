# -*- coding: utf-8 -*-
"""Enables code review using github."""
import zazu.imports
zazu.imports.lazy_import(locals(), [
    'git',
    'github',
    'os',
    'zazu.code_reviewer',
    'zazu.git_helper',
    'zazu.plugins.github_issue_tracker',
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2017'


class CodeReviewer(zazu.code_reviewer.CodeReviewer):
    """Implements zazu code review interface for GitHub."""

    def __init__(self, owner, repo, url=None):
        """Create a GitHubCodeReviewer.

        Args:
            owner (str): the github repo owner's username or organization name.
            repo (str): the github repo name.

        """
        self._owner = owner
        self._repo = repo
        self._url = url
        self._github = None

    def connect(self):
        """Get handle to ensure that github credentials are in place."""
        self._github_handle()

    def _github_handle(self):
        if self._github is None:
            self._github = zazu.github_helper.make_gh(self._url)
        return self._github

    def _github_repo(self):
        return self._github_handle().get_user(self._owner).get_repo(self._repo)

    def _normalize_head(self, head):
        if ':' not in head:
            head = '{}:{}'.format(self._owner, head)
        return head

    def review(self, status=github.GithubObject.NotSet, head=github.GithubObject.NotSet, base=github.GithubObject.NotSet):
        """Get reviews (pull requests) matching the search criteria."""
        head = github.GithubObject.NotSet if head is None else head
        base = github.GithubObject.NotSet if base is None else base
        status = github.GithubObject.NotSet if status is None else status
        head = self._normalize_head(head)
        matches = self._github_repo().get_pulls(state=status, head=head, base=base)
        return [GitHubCodeReview(m) for m in matches]

    def create_review(self, title, base, head, body, issue=None):
        """Create a new code review (pull request)."""
        head = self._normalize_head(head)
        if issue is not None:
            if isinstance(issue, zazu.plugins.github_issue_tracker.GitHubIssueAdaptor):
                issue_markdown_link = '#{}'.format(issue)
            else:
                issue_markdown_link = '[{}]({})'.format(issue, issue.browse_url)
            body += '\n\nFixes {}'.format(issue_markdown_link)
        return GitHubCodeReview(self._github_repo().create_pull(title=title, base=base, head=head, body=body))

    @staticmethod
    def from_config(config):
        """Make a GitHubCodeReviewer from a config."""
        # Get URL from current git repo:
        owner = config.get('owner', None)
        repo_name = config.get('repo', None)
        github_url = config.get('url', None)
        if owner is None or repo_name is None:
            repo = git.Repo(zazu.git_helper.get_repo_root(os.getcwd()))
            try:
                remote = repo.remotes.origin
            except AttributeError:
                raise zazu.code_reviewer.CodeReviewerError('No "origin" remote specified for this repo')
            owner, repo_name = zazu.github_helper.parse_github_url(remote.url)
        return CodeReviewer(owner, repo_name, github_url)

    @staticmethod
    def type():
        """Return the name of this CodeReviewer."""
        return 'github'


class GitHubCodeReview(zazu.code_reviewer.CodeReview):
    """Adapts a github pull request object into a zazu CodeReview object."""

    def __init__(self, github_pull_request):
        """Create a GitHubCodeReview interface by wrapping a pygithub PullRequest object."""
        self._pr = github_pull_request

    @property
    def name(self):
        """Get the string name of the code review."""
        return self._pr.title

    @property
    def status(self):
        """Get the string state of the code review."""
        return self._pr.state

    @property
    def description(self):
        """Get the string description of the code review."""
        return self._pr.body

    @property
    def assignee(self):
        """Get the string assignee of the code review."""
        return self._pr.assignee.login

    @property
    def head(self):
        """Return the branch name that is being merged from."""
        return self._pr.head.ref

    @property
    def base(self):
        """Return the branch name that is being merged to."""
        return self._pr.base.ref

    @property
    def browse_url(self):
        """Get the url to open to display the code review."""
        return self._pr.html_url

    @property
    def merged(self):
        """Return true if the code review has been merged."""
        return self._pr.merged

    @property
    def id(self):
        """Get the string id of the code review."""
        return str(self._pr.number)

    def __str__(self):
        """Create a string representation of the code review state."""
        return '#{} ({}, {}) {} -> {}'.format(self.id, self.status, 'merged' if self.merged else 'unmerged',
                                              self.head, self.base)
