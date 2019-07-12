# -*- coding: utf-8 -*-
import click
import click.testing
import keyring
import zazu.cli
import zazu.keychain

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


def mock_get_pass(component, name):
    returns = {
        'http://url':
            {
                'username': 'user',
                'password': 'password'
            }
    }
    return returns[component][name]


def test_credential_interface(mocker):
    mocker.patch('keyring.get_password', new=mock_get_pass)
    mocker.patch('keyring.set_password')
    mocker.patch('keyring.delete_password', side_effect=keyring.errors.PasswordDeleteError)
    interface = zazu.keychain.CredentialInterface('component', 'http://url', ['username'], ['password'], lambda x: True)
    assert not interface.validate()
    assert interface.load()
    assert interface.validate()
    assert interface['username'] == 'user'
    assert interface['password'] == 'password'
    assert set(interface.attributes()) == {'username', 'password'}
    assert interface.name() == 'component'
    assert interface.url() == 'http://url'
    interface['password'] = 'password2'
    assert interface['password'] == 'password2'
    interface.delete()
    deleted_call_args = {item[0] for item in keyring.delete_password.call_args_list}
    assert deleted_call_args == {('http://url', 'username'), ('http://url', 'password')}

    interface = zazu.keychain.CredentialInterface('component', 'http://url', ['username'], ['password'], lambda x: False)
    assert not interface.validate()
    assert interface.load()
    assert not interface.validate()


def test_set_interactive(mocker):
    mocker.patch('keyring.get_password', new=mock_get_pass)
    mocker.patch('keyring.set_password')
    mocker.patch('click.prompt', side_effect=['new_user', 'new_password'])
    mocker.patch('click.confirm', return_value=True)
    interface = zazu.keychain.CredentialInterface('component', 'http://url', ['username'], ['password'])
    interface.set_interactive()
    assert interface['username'] == 'new_user'
    assert interface['password'] == 'new_password'
    interface.offer_to_save()
    assert click.prompt.call_args_list[0][0] == ('Enter component username for http://url',)
    assert click.prompt.call_args_list[1][0] == ('Enter component password for http://url',)
    click.confirm.assert_called_once_with('Do you want to save these credentials?', default=True)
    assert keyring.set_password.call_args_list[0][0] == ('http://url', 'username', 'new_user')
    assert keyring.set_password.call_args_list[1][0] == ('http://url', 'password', 'new_password')


def test_keychain(mocker):
    mocker.patch('keyring.get_password', new=mock_get_pass)
    interface = zazu.keychain.CredentialInterface('component', 'http://url', ['username'], ['password'])
    mocker.patch('zazu.config.Config.credentials', return_value={interface.url(): interface})
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['keychain', '--list'])
    assert result.exit_code == 0


def test_keychain_bad_options(mocker):
    mocker.patch('keyring.get_password', new=mock_get_pass)
    interface = zazu.keychain.CredentialInterface('component', 'http://url', ['username'], ['password'])
    mocker.patch('zazu.config.Config.credentials', return_value={interface.url(): interface})
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['keychain'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['keychain', '--list', 'foo'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['keychain', 'foo'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['keychain', '--list', '--unset'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['keychain', '--unset'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['keychain', '--list'])
    assert result.exit_code == 0


def test_keychain_set_unset(mocker):
    mocker.patch('keyring.get_password', new=mock_get_pass)
    mocker.patch('keyring.set_password')
    mocker.patch('keyring.delete_password', side_effect=keyring.errors.PasswordDeleteError)
    mocker.patch('click.prompt', side_effect=['new_user', 'new_password'])
    interface = zazu.keychain.CredentialInterface('component', 'http://url', ['username'], ['password'])
    mocker.patch('zazu.config.Config.credentials', return_value={interface.url(): interface})
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['keychain', '--unset', 'http://foo'])
    assert result.exit_code != 0
    result = runner.invoke(zazu.cli.cli, ['keychain', '--unset', 'http://url'])
    assert result.exit_code == 0
    deleted_call_args = {item[0] for item in keyring.delete_password.call_args_list}
    assert deleted_call_args == {('http://url', 'username'), ('http://url', 'password')}
    result = runner.invoke(zazu.cli.cli, ['keychain', '--set', 'http://url'])
    assert result.exit_code == 0
    assert click.prompt.call_args_list[0][0] == ('Enter component username for http://url',)
    assert click.prompt.call_args_list[1][0] == ('Enter component password for http://url',)
    mocker.patch('click.prompt', side_effect=['new_user', 'new_password'])
    interface._validator_callback = lambda x: False
    result = runner.invoke(zazu.cli.cli, ['keychain', '--set', 'http://url'])
    assert result.exit_code != 0


def test_complete_entry(mocker):
    interface = zazu.keychain.CredentialInterface('component', 'http://url', ['username'], ['password'])
    mocker.patch('zazu.config.Config.credentials', return_value={interface.url(): interface})
    assert zazu.keychain.complete_entry(None, [], 'htt') == [('http\\://url', 'component')]
