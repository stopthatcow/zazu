# -*- coding: utf-8 -*-
"""Credential functions for zazu."""
import zazu.imports
zazu.imports.lazy_import(locals(), [
    'click',
    'keyring',
    'zazu.util',
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


def get_user_pass_credentials(url, use_saved=True, offer_to_save=True):
    """Retrieve a stored user/password for a named component or offers to store a new set."""
    username = None
    password = None
    if use_saved:
        username = get_user(url)
        password = get_password(url)
    if password is None or username is None:
        username = zazu.util.prompt('Username for {}'.format(url), expected_type=str)
        password = click.prompt('Password for {} at {}'.format(
            username, url), type=str, hide_input=True)
        if offer_to_save and click.confirm('Do you want to save these credentials?', default=True):
            set_user(url, username)
            set_password(url, password)
            click.echo('saved.')
    return username, password


def get_user(url):
    """Get the stored username for a given URL from the keychain."""
    return keyring.get_password(url, 'username')


def set_user(url, username):
    """Store a username to the keychain for a given URL."""
    return keyring.set_password(url, 'username', username)


def get_password(url):
    """Get the stored password for a given URL from the keychain."""
    return keyring.get_password(url, 'password')


def set_password(url, password):
    """Store a password to the keychain for a given URL."""
    return keyring.set_password(url, 'password', password)
