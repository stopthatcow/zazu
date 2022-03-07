# -*- coding: utf-8 -*-
import tests.conftest as conftest
import github
import pytest
import zazu.github_helper
import zazu.plugins.github_scm_host

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@pytest.fixture
def scm_host_mock(mocker):
    return zazu.plugins.github_scm_host.ScmHost('stopthatcow')


mock_repo_dict = {
    'name': 'zazu',
    'full_name': 'stopthatcow/zazu',
    'description': 'description',
    'html_url': 'https://github.com/stopthatcow/zazu',
    'ssh_url': 'ssh://git@github.com/stopthatcow/zazu'
}
mock_repo = conftest.dict_to_obj(mock_repo_dict)


def test_github_scm_host_get_repos(mocker, scm_host_mock):
    github_mock = mocker.Mock('github.Github', autospec=True)
    user_mock = mocker.Mock('github.NamedUser.NamedUser', autospec=True)
    github_mock.get_user = mocker.Mock('github.Github.get_user', autospec=True, return_value=user_mock)
    user_mock.get_repos = mocker.Mock('github.NamedUser.NamedUser.get_repos', autospec=True, return_value=[mock_repo])
    mocker.patch('zazu.github_helper.make_gh', return_value=github_mock)
    scm_host_mock.connect()
    repos = list(scm_host_mock.repos())
    github_mock.get_user.assert_called_once_with()
    user_mock.get_repos.assert_called_once()
    assert len(repos) == 1
    assert repos[0].name == 'zazu'


def test_github_scm_host_get_repos_error(mocker, scm_host_mock):
    github_mock = mocker.Mock('github.Github', autospec=True)
    user_mock = mocker.Mock('github.NamedUser.NamedUser', autospec=True)
    github_mock.get_user = mocker.Mock('github.Github.get_user', autospec=True, return_value=user_mock)
    user_mock.get_repos = mocker.Mock('github.NamedUser.NamedUser.get_repos', autospec=True, side_effect=github.GithubException(404, {}, ''))
    mocker.patch('zazu.github_helper.make_gh', return_value=github_mock)
    scm_host_mock.connect()
    with pytest.raises(zazu.scm_host.ScmHostError) as e:
        list(scm_host_mock.repos())
    assert '404' in str(e.value)


def test_from_config(git_repo):
    with zazu.util.cd(git_repo.working_tree_dir):
        uut = zazu.plugins.github_scm_host.ScmHost.from_config({'user': 'stopthatcow',
                                                                'type': 'github'})
        assert uut.type() == 'github'


def test_github_scm_host_repo_adaptor():
    uut = zazu.plugins.github_scm_host.GitHubScmRepoAdaptor(mock_repo)
    assert uut.name == 'zazu'
    assert uut.description == 'description'
    assert uut.id == 'stopthatcow/zazu'
    assert uut.browse_url == 'https://github.com/stopthatcow/zazu'
    assert uut.ssh_url == 'ssh://git@github.com/stopthatcow/zazu'
    assert str(uut) == uut.id
    assert repr(uut) == uut.id
