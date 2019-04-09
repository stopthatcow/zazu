# -*- coding: utf-8 -*-
import click
import keyring
import zazu.credential_helper

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


def mock_get_pass(component, name):
    returns = {
        'component':
            {
                'username': 'user',
                'password': 'password'
            }
    }
    return returns[component][name]


def test_user_pass_credentials_saved(mocker):
    mocker.patch('keyring.get_password', new=mock_get_pass)
    mocker.patch('keyring.set_password')
    creds = zazu.credential_helper.get_user_pass_credentials('component', use_saved=True)
    assert creds == ('user', 'password')


def test_user_pass_credentials_prompt(mocker):
    mocker.patch('keyring.get_password', new=mock_get_pass)
    mocker.patch('keyring.set_password')
    mocker.patch('zazu.util.prompt', return_value='new_user')
    mocker.patch('click.prompt', return_value='new_password')
    mocker.patch('click.confirm', return_value=True)
    creds = zazu.credential_helper.get_user_pass_credentials('component', use_saved=False)
    assert creds == ('new_user', 'new_password')
    zazu.util.prompt.assert_called_once_with('Username for component', expected_type=str)
    click.prompt.assert_called_once_with('Password for new_user at component', type=str, hide_input=True)
    click.confirm.assert_called_once_with('Do you want to save these credentials?', default=True)
    assert keyring.set_password.call_args_list[0][0] == ('component', 'username', 'new_user')
    assert keyring.set_password.call_args_list[1][0] == ('component', 'password', 'new_password')
