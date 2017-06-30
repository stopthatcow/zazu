# -*- coding: utf-8 -*-
"""credential functions for zazu"""
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'keyring'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def get_user_pass_credentials(component, use_saved=True):
    """Retrieves a stored user/password for a named component or offers to store a new set"""
    keyring_user = component.lower() + '_user'
    keyring_password = component.lower() + '_password'
    user = None
    password = None
    if use_saved:
        user = keyring.get_password(component, keyring_user)
        password = keyring.get_password(component, keyring_password)
    if user is None or password is None:
        user = zazu.util.prompt('{} username'.format(component), expected_type=str)
        password = click.prompt('{} password'.format(
            component), type=str, hide_input=True)
        if click.confirm('Do you want to save these credentials?', default=True):
            keyring.set_password(component, keyring_user, user)
            keyring.set_password(component, keyring_password, password)
            click.echo("saved.")
    return user, password
