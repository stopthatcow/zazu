# -*- coding: utf-8 -*-
"""Clasess that adapt GitHub for use as a zazu ScmHost."""
import zazu.imports
zazu.imports.lazy_import(locals(), [
    'github',
    'os',
    'zazu.github_helper',
    'zazu.scm_host',
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


class ScmHost(zazu.scm_host.ScmHost):
    """Implements zazu SCM host interface for GitHub."""

    def __init__(self, user, url=None):
        """Create a ScmHost for GitHub.

        Args:
            user (str): the github username.

        """
        self._github_handle = None
        self._url = url

    def connect(self):
        """Get handle to ensure that github credentials are in place."""
        self._github()

    def _github(self):
        if self._github_handle is None:
            self._github_handle = zazu.github_helper.make_gh(self._url)
        return self._github_handle

    def repos(self):
        """List repos available to this user."""
        try:
            for r in self._github().get_user().get_repos():
                yield GitHubScmRepoAdaptor(r)
        except github.GithubException as e:
            raise zazu.scm_host.ScmHostError(str(e))

    @staticmethod
    def from_config(config):
        """Make a GitHubScmHost from a config."""
        # Get URL from current git repo:
        return ScmHost(user=config['user'],
                       url=config.get('url', None))

    @staticmethod
    def type():
        """Return the name of this ScmHost type."""
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
        """Get the url to open to display the repo."""
        return self._github_repo.html_url

    @property
    def ssh_url(self):
        """Get the ssh url to clone the repo."""
        return self._github_repo.ssh_url
