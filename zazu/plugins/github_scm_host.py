# -*- coding: utf-8 -*-
"""Clasess that adapt GitHub for use as a zazu VersionControlHost."""
import zazu.github_helper
import zazu.scm_host
import zazu.util
zazu.util.lazy_import(locals(), [
    'github',
    'os'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class GitHubVersionControlHost(zazu.scm_host.ScmHost):
    """Implements zazu VersionControlHost interface for GitHub."""

    def __init__(self, user):
        """Create a GitHubVersionControlHost.

        Args:
            user (str): the github username.
        """
        self._user = user
        self._github_handle = None

    def connect(self):
        """Get handle to ensure that github credentials are in place."""
        self._github()

    def _github(self):
        if self._github_handle is None:
            self._github_handle = zazu.github_helper.make_gh()
        return self._github_handle

    def repos(self):
        """List repos available to this user."""
        try:
            for r in self._github().get_user(self._user).get_repos():
                yield GitHubScmRepoAdaptor(r)
        except github.GithubException as e:
            raise zazu.scm_host.ScmHostError(str(e))

    @staticmethod
    def from_config(config):
        """Make a GitHubVersionControlHost from a config."""
        # Get URL from current git repo:
        return GitHubVersionControlHost(user=config['user'])

    @staticmethod
    def type():
        """Return the name of this VersionControlHost type."""
        return 'github'


class GitHubScmRepoAdaptor(zazu.scm_host.ScmHostRepo):
    """Wraps a repo returned from the GirHub api and adapts it to the zazu.scm_host.ScmHostRepo interface."""

    def __init__(self, github_repo):
        """Create a GitHubScmRepoAdaptor by wrapping a GitHub Repo object.

        Args:
            github_repo: GitHub repo handle.
        """
        self._github_repo = github_repo

    @property
    def name(self):
        """Get the name of the repo."""
        return self._github_repo.name

    @property
    def id(self):
        """Get the full name of the repo as the id."""
        return self._github_repo.full_name

    @property
    def description(self):
        """Get the description of the repo."""
        return self._github_repo.description

    @property
    def browse_url(self):
        """Get the url to open to display the issue."""
        return self._github_repo.html_url

    @property
    def ssh_url(self):
        """Get the ssh url to clone the repo."""
        return self._github_repo.ssh_url
