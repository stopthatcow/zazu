# -*- coding: utf-8 -*-
"""credential functions for zazu"""
import keyring
import click
import util


def get_user_pass_credentials(component, use_saved=True):
    keyring_user = component.lower() + '_user'
    keyring_password = component.lower() + '_password'
    user = None
    password = None
    if use_saved:
        user = keyring.get_password(component, keyring_user)
        password = keyring.get_password(component, keyring_password)
    if user is None or password is None:
        user = util.prompt('{} username'.format(component), type=str)
        password = click.prompt('{} password'.format(
            component), type=str, hide_input=True)
        if click.confirm('Do you want to save these credentials?', default=True):
            keyring.set_password(component, keyring_user, user)
            keyring.set_password(component, keyring_password, password)
            click.echo("saved.")
    return user, password
