# -*- coding: utf-8 -*-
import click
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


def test_make_gh_bad_token(mocker):
    mocker.patch('keyring.get_password', return_value=None)
    mocker.patch('keyring.set_password')
    mocker.patch('zazu.github_helper.make_gh_token', return_value='token')
    mocker.patch('click.echo')
    mocker.patch('github.Github.get_user', side_effect=[github.BadCredentialsException('', '')])
    zazu.github_helper.make_gh()
    click.echo.calls[0][1] == ('No saved GitHub token found in keychain, lets add one...',)
    click.echo.calls[1][1] == ('GitHub token rejected, you will need to create a new token.',)


class MockResponse(object):

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
            return MockResponse(json={'message': 'Must specify two-factor authentication OTP code.'}, status_code=401)
        else:
            assert headers['X-GitHub-OTP'] == 'token'
            return MockResponse(json={'token': 'token'}, status_code=201)

    mocker.patch('click.prompt', side_effect=['user', 'password', 'token'], autospec=True)
    mocker.patch('click.confirm', return_value=True)
    mocker.patch('keyring.set_password')

    with mock_post(mocker, 'https://api.github.com/authorizations', mocker.Mock(wraps=require_otp)) as post_auth:
        assert 'token' == zazu.github_helper.make_gh_token()
        post_auth.call_count == 2


def test_make_gh_token_otp_exists(mocker):
    def token_exists(uri, headers={}, auth=(), json={}):
        assert ('user', 'password') == auth
        return MockResponse(json={}, status_code=422)
    mocker.patch('click.prompt', side_effect=['user', 'password', 'token'], autospec=True)
    mocker.patch('click.confirm', return_value=True)

    with mock_post(mocker, 'https://api.github.com/authorizations', mocker.Mock(wraps=token_exists)) as post_auth:
        assert 'token' == zazu.github_helper.make_gh_token()
        post_auth.call_count == 1


def test_make_gh_token_otp_unknown_error(mocker):
    mocker.patch('click.confirm', return_value=True)
    mocker.patch('click.prompt', side_effect=['user', 'password'], autospec=True)
    with mock_post(mocker, 'https://api.github.com/authorizations', mocker.Mock(return_value=MockResponse(json={}, status_code=400))) as post_auth:
        with pytest.raises(Exception):
            zazu.github_helper.make_gh_token()
            post_auth.call_count == 1


def test_make_gh_token_try_again(mocker):
    def normal_auth(uri, headers={}, auth=(), json={}):
        if ('user', 'password') == auth:
            return MockResponse(json={'token': 'token'}, status_code=201)
        return MockResponse(json={'message': ''}, status_code=401)

    mocker.patch('click.prompt', side_effect=['bad_user', 'bad_password', 'user', 'password', 'user', 'password'], autospec=True)
    mocker.patch('keyring.set_password')
    mocker.patch('click.confirm', return_value=True)
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


def test_mock_and_validate_credentials(mocker):
    mocker.patch('github.Github.get_user', side_effect=[github.BadCredentialsException('', ''), mocker.Mock()])
    credentials = zazu.github_helper.token_credential_interface()
    credentials['token'] = 'token'
    assert not credentials.validate()
    assert credentials.validate()


def test_validate_credentials(mocker):
    mock_gh = mocker.Mock()
    mock_gh.get_user = mocker.Mock(side_effect=github.BadCredentialsException('', ''))
    assert not zazu.github_helper.validate_credentials(mock_gh)
