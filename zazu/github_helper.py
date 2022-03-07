# -*- coding: utf-8 -*-
"""Github functions for zazu."""
import zazu.imports
zazu.imports.lazy_import(locals(), [
    'click',
    'getpass',
    'github',
    're',
    'requests',
    'socket',
    'zazu.util',
    'zazu.credential_helper',
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


GITHUB_API_URL = 'https://api.github.com'


def make_gh_token(api_url=None):
    """Make new GitHub token."""
    click.echo('Go to https://github.com/settings/tokens to generate a new one with "repo" scope')
    return zazu.util.prompt('Enter new token')


def make_gh(api_url=None):
    """Make github object with token from the keychain."""
    if api_url is None:
        api_url = GITHUB_API_URL
    import keyring  # For some reason this doesn't play nicely with threads on lazy import.
    gh = None
    token = keyring.get_password(api_url, 'token')
    if token is None:
        click.echo('No saved GitHub token found in keychain, lets add one...')
    while gh is None:
        try:
            if token is None:
                token = make_gh_token(api_url)
                gh = github.Github(base_url=api_url, login_or_token=token)
                keyring.set_password(api_url, 'token', token)
            else:
                gh = github.Github(base_url=api_url, login_or_token=token)
        except github.BadCredentialsException:
            click.echo("GitHub token rejected, you will need to create a new token.")
            token = None
    return gh


def parse_github_url(url):
    """Parse github url into organization and repo name."""
    tokens = re.split('/|:', url.replace('.git', ''))
    repo = tokens.pop()
    organization = tokens.pop()
    return organization, repo
