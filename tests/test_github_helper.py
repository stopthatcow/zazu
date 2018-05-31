# -*- coding: utf-8 -*-
import contextlib
import github
import keyring  # NOQA
import pytest
import requests  # NOQA
import zazu.github_helper

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_make_gh_with_sacved_credentials(mocker):
    mocker.patch('keyring.get_password', return_value='token')
    mocker.patch('keyring.set_password')
    mocker.patch('github.Github')
    zazu.github_helper.make_gh()
    github.Github.assert_called_once_with('token')


def test_make_gh_with_no_credentials(mocker):
    mocker.patch('keyring.get_password', return_value=None)
    mocker.patch('keyring.set_password')
    mocker.patch('zazu.github_helper.make_gh_token', return_value='token')
    mocker.patch('github.Github')
    zazu.github_helper.make_gh()
    zazu.github_helper.make_gh_token.assert_called_once()
    github.Github.assert_called_once_with('token')


def test_make_gh_with_bad_token(mocker):
    def side_effect(token):
        if token == 'token':
            raise github.BadCredentialsException('status', 'data')
        return token
    mocker.patch('keyring.get_password', return_value='token')
    mocker.patch('keyring.set_password')
    mocker.patch('zazu.github_helper.make_gh_token', return_value='token2')
    mocker.patch('github.Github', side_effect=side_effect)
    zazu.github_helper.make_gh()
    calls = github.Github.call_args_list
    assert github.Github.call_count == 2
    assert calls[0] == mocker.call('token')
    assert calls[1] == mocker.call('token2')


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


def test_make_gh_token_otp(mocker):
    def require_otp(uri, headers={}, auth=(), json={}):
        assert ('user', 'password') == auth
        if 'X-GitHub-OTP' not in headers:
            return MockResponce(json={'message': 'Must specify two-factor authentication OTP code.'}, status_code=401)
        else:
            assert headers['X-GitHub-OTP'] == 'token'
            return MockResponce(json={'token': 'token'}, status_code=201)

    mocker.patch('zazu.util.prompt', side_effect=['user', 'token'], autospec=True)
    mocker.patch('click.prompt', return_value='password', autospec=True)
    mocker.patch('keyring.set_password')

    with mock_post(mocker, 'https://api.github.com/authorizations', mocker.Mock(wraps=require_otp)) as post_auth:
        assert 'token' == zazu.github_helper.make_gh_token()
        post_auth.call_count == 2


def test_make_gh_token_otp_exists(mocker):
    def token_exists(uri, headers={}, auth=(), json={}):
        assert ('user', 'password') == auth
        return MockResponce(json={}, status_code=422)
    mocker.patch('zazu.util.prompt', side_effect=['user', 'token'], autospec=True)
    mocker.patch('click.prompt', return_value='password', autospec=True)

    with mock_post(mocker, 'https://api.github.com/authorizations', mocker.Mock(wraps=token_exists)) as post_auth:
        assert 'token' == zazu.github_helper.make_gh_token()
        post_auth.call_count == 1


def test_make_gh_token_otp_unknown_error(mocker):
    mocker.patch('zazu.util.prompt', return_value='user', autospec=True)
    mocker.patch('click.prompt', return_value='password', autospec=True)
    with mock_post(mocker, 'https://api.github.com/authorizations', mocker.Mock(return_value=MockResponce(json={}, status_code=400))) as post_auth:
        with pytest.raises(Exception):
            zazu.github_helper.make_gh_token()
            post_auth.call_count == 1


def test_make_gh_token_try_again(mocker):
    def normal_auth(uri, headers={}, auth=(), json={}):
        if ('user', 'password') == auth:
            return MockResponce(json={'token': 'token'}, status_code=201)
        return MockResponce(json={'message': ''}, status_code=401)

    mocker.patch('zazu.util.prompt', side_effect=['bad_user', 'user'], autospec=True)
    mocker.patch('click.prompt', side_effect=['bad_password', 'password'], autospec=True)
    mocker.patch('keyring.set_password')
    with mock_post(mocker, 'https://api.github.com/authorizations', mocker.Mock(wraps=normal_auth)) as post_auth:
        zazu.github_helper.make_gh_token()
        post_auth.call_count == 2


def test_parse_github_url():
    owner = 'stopthatcow'
    name = 'zazu'
    url = 'ssh://git@github.com/{}/{}'.format(owner, name)
    owner_out, name_out = zazu.github_helper.parse_github_url(url)
    assert owner_out == owner
    assert name_out == name
