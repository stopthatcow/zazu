# -*- coding: utf-8 -*-
"""Enables code review using github"""
import zazu.code_reviewer
import zazu.util
zazu.util.lazy_import(locals(), [
    'git',
    'github',
    'os'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class GithubCodeReviewer(zazu.code_reviewer.CodeReviewer):
    """Implements zazu code review interface for GitHub"""

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

    def get_review(self, state, base, head):
        if ':' not in head:
            head = '{}:{}'.format(self._org, head)
        existing_pulls = self.github_repo().get_pulls(state=state, head=head, base=base)
        try:
            return existing_pulls[0]
        except IndexError:
            return None

    def create_review(self, title, base, head, body):
        if ':' not in head:
            head = '{}:{}'.format(self._org, head)
        # TODO(nwiles): Make adaptor class for PR.
        return self.github_repo().create_pull(title=title, base=base, head=head, body=body)

    @staticmethod
    def from_config(config):
        """Makes a GithubCodeReviewer from a config"""
        # Get URL from current git repo:
        owner = config.get('owner', None)
        repo_name = config.get('repo', None)
        if owner is None or repo_name is None:
            repo = git.Repo(zazu.git_helper.get_repo_root(os.getcwd()))
            try:
                remote = repo.remotes.origin
            except AttributeError:
                raise zazu.code_review.CodeReviewerError('No "origin" remote specified for this repo')
            owner, repo_name = zazu.github_helper.parse_github_url(remote.url)
        return GithubCodeReviewer(owner, repo_name)

    @staticmethod
    def type():
        return 'github'
