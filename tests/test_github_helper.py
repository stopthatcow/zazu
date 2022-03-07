# -*- coding: utf-8 -*-
import contextlib
import github
import keyring  # NOQA
import pytest
import requests  # NOQA
import zazu.github_helper

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_make_gh_with_saved_credentials(mocker):
    mocker.patch('keyring.get_password', return_value='token')
    mocker.patch('keyring.set_password')
    mocker.patch('github.Github')
    custom_url = 'https://custom.github.com'
    zazu.github_helper.make_gh(custom_url)
    github.Github.assert_called_once_with(base_url=custom_url, login_or_token='token')


def test_make_gh_with_no_credentials(mocker):
    mocker.patch('keyring.get_password', return_value=None)
    mocker.patch('keyring.set_password')
    mocker.patch('zazu.github_helper.make_gh_token', return_value='token')
    mocker.patch('github.Github')
    zazu.github_helper.make_gh()
    zazu.github_helper.make_gh_token.assert_called_once()
    github.Github.assert_called_once_with(base_url=zazu.github_helper.GITHUB_API_URL, login_or_token='token')


def test_make_gh_with_bad_token(mocker):
    def side_effect(base_url, login_or_token):
        if login_or_token == 'token':
            raise github.BadCredentialsException('status', 'data', [])
        return login_or_token
    mocker.patch('keyring.get_password', return_value='token')
    mocker.patch('keyring.set_password')
    mocker.patch('zazu.github_helper.make_gh_token', return_value='token2')
    mocker.patch('github.Github', side_effect=side_effect)
    zazu.github_helper.make_gh()
    calls = github.Github.call_args_list
    assert github.Github.call_count == 2
    assert calls[0] == mocker.call(base_url=zazu.github_helper.GITHUB_API_URL,
                                   login_or_token='token')
    assert calls[1] == mocker.call(base_url=zazu.github_helper.GITHUB_API_URL,
                                   login_or_token='token2')


class MockResponce(object):

    def __init__(self, status_code, json=None):
        self._json = json
        self.status_code = status_code

    def json(self):
        return self._json


request_mocks = {}


@contextlib.contextmanager
def mock_post(mocker, uri, mock):
    mocker.patch('requests.post', new=handle_post)
    request_mocks[('POST', uri)] = mock
    yield mock
    del request_mocks[('POST', uri)]


def handle_post(*args, **kwargs):
    entry = request_mocks[('POST', args[0])]
    return entry(*args, **kwargs)

def test_parse_github_url():
    owner = 'stopthatcow'
    name = 'zazu'
    url = 'ssh://git@github.com/{}/{}'.format(owner, name)
    owner_out, name_out = zazu.github_helper.parse_github_url(url)
    assert owner_out == owner
    assert name_out == name
