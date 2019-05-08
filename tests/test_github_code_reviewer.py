# -*- coding: utf-8 -*-
import tests.conftest
import pytest
import zazu.util
import zazu.plugins.github_code_reviewer

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


class MockRepo(object):

    def create_pull(self, *args, **kwargs):
        return tests.conftest.dict_to_obj({
            'number': 3,
            'title': kwargs['title'],
            'state': 'closed',
            'resolution': {
                'name': 'Done'
            },
            'body': kwargs['body'],
            'assignee': {
                'login': 'assignee'
            },
            'head': {
                'ref': kwargs['head']
            },
            'base': {
                'ref': kwargs['base']
            },
            'html_url': 'browse_url',
            'merged': False
        })

    def get_pulls(self, state, head, base):
        return [self.create_pull(title='title', body='body', head='foo:head', base='base')]


class MockUser(object):

    def get_repo(self, repo):
        return MockRepo()


class MockGitHub(object):

    def get_user(self, user):
        return MockUser()


def test_github_issue_tracker_auto_url(repo_with_github_as_origin):
    dir = repo_with_github_as_origin.working_tree_dir
    with zazu.util.cd(dir):
        uut = zazu.plugins.github_code_reviewer.CodeReviewer.from_config({})
        assert uut._owner == 'stopthatcow'
        assert uut._repo == 'zazu'


def test_github_issue_tracker_no_origin(git_repo):
    dir = git_repo.working_tree_dir
    with zazu.util.cd(dir):
        with pytest.raises(zazu.code_reviewer.CodeReviewerError):
            zazu.plugins.github_code_reviewer.CodeReviewer.from_config({})


def test_credentials(mocker, repo_with_github_as_origin):
    with zazu.util.cd(repo_with_github_as_origin.working_tree_dir):
        mocker.patch('zazu.github_helper.token_credential_interface')
        uut = zazu.plugins.github_code_reviewer.CodeReviewer.from_config({})
        uut.credentials()
        zazu.github_helper.token_credential_interface.assert_called_once()


mock_review_dict = {
    'number': 3,
    'title': 'name',
    'state': 'closed',
    'resolution': {
        'name': 'Done'
    },
    'body': 'description',
    'assignee': {
        'login': 'assignee'
    },
    'head': {
        'ref': 'foo:head'
    },
    'base': {
        'ref': 'base'
    },
    'html_url': 'browse_url',
    'merged': False
}
mock_review_obj = tests.conftest.dict_to_obj(mock_review_dict)
mock_gihub_review = zazu.plugins.github_code_reviewer.GitHubCodeReview(mock_review_obj)


class MockNonGithubIssue(object):

    @property
    def browse_url(self):
        return 'http://url'

    def __str__(self):
        return '3'


class MockGithubIssue(zazu.plugins.github_issue_tracker.GitHubIssueAdaptor):

    def __init__(self):
        super(MockGithubIssue, self).__init__(None)

    def __str__(self):
        return '3'


def test_github_issue_tracker(mocker):
    mocker.patch('zazu.github_helper.make_gh', return_value=MockGitHub())
    uut = zazu.plugins.github_code_reviewer.CodeReviewer.from_config({'owner': 'foo',
                                                                      'repo': 'bar'})
    assert uut._owner == 'foo'
    assert uut._repo == 'bar'
    uut.connect()
    assert uut.type() == 'github'

    review = uut.create_review(title='title', base='base', head='head', body='body', issue=None)
    pulls = uut.review(base='base', head='head')
    assert len(pulls) == 1
    review = uut.create_review(title='title', base='base', head='head', body='body', issue=MockNonGithubIssue())
    assert '[3](http://url)' in review.description
    review = uut.create_review(title='title', base='base', head='head', body='body', issue=MockGithubIssue())
    assert '#3' in review.description


def test_github_code_review_adaptor():
    uut = mock_gihub_review
    assert uut.name == 'name'
    assert uut.status == 'closed'
    assert uut.description == 'description'
    assert uut.assignee == 'assignee'
    assert uut.head == 'foo:head'
    assert uut.base == 'base'
    assert uut.browse_url == 'browse_url'
    assert not uut.merged
    assert str(uut) == '#3 (closed, unmerged) foo:head -> base'
