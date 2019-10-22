# -*- coding: utf-8 -*-
import tests.conftest as conftest
import copy
import github
import pytest
import zazu.git_helper
import zazu.github_helper
import zazu.plugins.github_issue_tracker

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@pytest.fixture
def tracker_mock():
    return zazu.plugins.github_issue_tracker.IssueTracker('stopthatcow', 'zazu')


@pytest.fixture
def mocked_github_issue_tracker(mocker, tracker_mock):
    github_mock = mocker.Mock('github.Github', autospec=True)
    mocker.patch('zazu.github_helper.make_gh', return_value=github_mock)
    repo_obj_mock = mocker.Mock('github.Repository', autospec=True)
    mocker.patch('zazu.plugins.github_issue_tracker.IssueTracker._github_repo', return_value=repo_obj_mock)
    tracker_mock._github = repo_obj_mock
    return tracker_mock


mock_issue_dict = {
    'number': 1,
    'title': 'name',
    'state': 'closed',
    'body': 'description',
    'assignees': [{'login': 'assignee'}],
    'html_url': 'https://github.com/stopthatcow/zazu/issues/1'
}
mock_issue = conftest.dict_to_obj(mock_issue_dict)


def test_github_issue_tracker_issue(mocker, mocked_github_issue_tracker):
    mocked_github_issue_tracker._github.get_issue = mocker.Mock(return_value=mock_issue)
    mocked_github_issue_tracker.connect()
    mocked_github_issue_tracker.issue('1')
    assert mocked_github_issue_tracker._github.get_issue.call_count == 1
    mocked_github_issue_tracker._github.get_issue.assert_called_once_with(1)


def test_github_issue_tracker_issue_error(mocker, mocked_github_issue_tracker):
    mocked_github_issue_tracker._github.get_issue = mocker.Mock(side_effect=github.GithubException(404, {}))
    with pytest.raises(zazu.issue_tracker.IssueTrackerError) as e:
        mocked_github_issue_tracker.issue('1')
    assert '404' in str(e.value)


def test_github_issue_tracker_create_issue_error(mocker, mocked_github_issue_tracker):
    mocked_github_issue_tracker._github.create_issue = mocker.Mock(side_effect=github.GithubException(404, {}))
    with pytest.raises(zazu.issue_tracker.IssueTrackerError) as e:
        mocked_github_issue_tracker.create_issue('', '', '', '', '')
    assert '404' in str(e.value)


def test_github_issue_tracker_create_issue(mocker, mocked_github_issue_tracker):
    mocked_github_issue_tracker._github.create_issue = mocker.Mock(return_value=mock_issue)
    mocked_github_issue_tracker.create_issue('project', 'issue_type', 'summary', 'description', 'component')
    zazu.plugins.github_issue_tracker.IssueTracker._github_repo.create_issue.call_count == 1


def test_github_issue_tracker_list_issues(mocker, mocked_github_issue_tracker):
    mocked_github_issue_tracker._github.get_issues = mocker.Mock(return_value=[mock_issue])
    mocked_github_issue_tracker.get_issues = mocker.Mock()
    zazu.plugins.github_issue_tracker.IssueTracker._github_repo.get_issues.call_count == 1


def test_github_issue_tracker_list_issues_error(mocker, mocked_github_issue_tracker):
    mocked_github_issue_tracker._github.get_issues = mocker.Mock(side_effect=github.GithubException(404, {}))
    with pytest.raises(zazu.issue_tracker.IssueTrackerError) as e:
        mocked_github_issue_tracker.issues()
    assert '404' in str(e.value)


def test_from_config_no_project(git_repo):
    with zazu.util.cd(git_repo.working_tree_dir):
        with pytest.raises(zazu.issue_tracker.IssueTrackerError) as e:
            zazu.plugins.github_issue_tracker.IssueTracker.from_config({})
        assert str(e.value) == 'No "origin" remote specified for this repo'


def test_github_issue_tracker_get_repo(mocker, tracker_mock):
    github_mock = mocker.Mock('github.Github', autospec=True)
    user_mock = mocker.Mock('github.NamedUser.NamedUser', autospec=True)
    github_mock.get_user = mocker.Mock('github.Github.get_user', autospec=True, return_value=user_mock)
    user_mock.get_repo = mocker.Mock('ggithub.NamedUser.NamedUser.get_repo', autospec=True)
    mocker.patch('zazu.github_helper.make_gh', return_value=github_mock)
    tracker_mock._github_repo()
    github_mock.get_user.assert_called_once_with('stopthatcow')
    user_mock.get_repo.assert_called_once_with('zazu')


def test_from_config(git_repo):
    with zazu.util.cd(git_repo.working_tree_dir):
        uut = zazu.plugins.github_issue_tracker.IssueTracker.from_config({'owner': 'stopthatcow',
                                                                          'repo': 'zazu'})
        assert uut._owner == 'stopthatcow'
        assert uut._repo == 'zazu'
        assert not uut.default_project()
        assert ['issue'] == uut.issue_types()
        assert [] == uut.issue_components()
        assert uut.type() == 'github'


def test_from_config_from_origin(repo_with_github_as_origin):
    with zazu.util.cd(repo_with_github_as_origin.working_tree_dir):
        uut = zazu.plugins.github_issue_tracker.IssueTracker.from_config({})
        assert uut._owner == 'stopthatcow'
        assert uut._repo == 'zazu'
        assert not uut.default_project()
        assert ['issue'] == uut.issue_types()
        assert [] == uut.issue_components()


def test_credentials(mocker, git_repo):
    with zazu.util.cd(git_repo.working_tree_dir):
        mocker.patch('zazu.github_helper.token_credential_interface')
        uut = zazu.plugins.github_issue_tracker.IssueTracker.from_config({'owner': 'stopthatcow',
                                                                          'repo': 'zazu'})
        uut.credentials()
        zazu.github_helper.token_credential_interface.assert_called_once()


def test_github_validate_id_format(tracker_mock):
    uut = tracker_mock
    uut.validate_id_format('10')
    with pytest.raises(zazu.issue_tracker.IssueTrackerError) as e:
        uut.validate_id_format('lc-10')
    assert str(e.value) == 'issue id "lc-10" is not numeric'
    with pytest.raises(zazu.issue_tracker.IssueTrackerError):
        uut.validate_id_format('10a')


def test_assign(mocker, tracker_mock):
    uut = tracker_mock
    uut._user = 'me'
    mock_gh_issue = mocker.Mock()
    mock_gh_issue.edit = mocker.Mock()
    mock_gh_issue_wrapper = mocker.Mock()
    mock_gh_issue_wrapper._github_issue = mock_gh_issue
    uut.assign_issue(mock_gh_issue_wrapper, uut.user())
    mock_gh_issue.edit.assert_called_once_with(assignee='me')


def test_github_issue_adaptor():
    uut = zazu.plugins.github_issue_tracker.GitHubIssueAdaptor(mock_issue)
    assert uut.name == 'name'
    assert uut.status == 'closed'
    assert uut.description == 'description'
    assert uut.assignee == 'assignee'
    assert uut.closed
    assert uut.type == 'issue'
    assert uut.browse_url == 'https://github.com/stopthatcow/zazu/issues/1'
    assert uut.id == '1'
    assert str(uut) == uut.id
    mock_issue2 = copy.copy(mock_issue)
    mock_issue2.number = 2
    uut2 = zazu.plugins.github_issue_tracker.GitHubIssueAdaptor(mock_issue2)
    assert uut < uut2
    assert uut < 2
    assert uut < '2'
