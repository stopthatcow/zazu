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
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


GITHUB_API_URL = 'https://api.github.com'


def make_gh_token(api_url=GITHUB_API_URL):
    """Make new GitHub token."""
    add_auth = {
        'scopes': [
            'repo'
        ],
        'note': 'zazu for {}@{}'.format(getpass.getuser(), socket.gethostname())
    }
    token = None
    while token is None:
        user, password = zazu.credential_helper.get_user_pass_credentials(api_url, offer_to_save=False)
        r = requests.post('{}/authorizations'.format(api_url), json=add_auth, auth=(user, password))
        if r.status_code == 401:
            if 'Must specify two-factor authentication OTP code.' in r.json()['message']:
                headers = {'X-GitHub-OTP': zazu.util.prompt('GitHub two-factor code (6 digits)', expected_type=str)}
                r = requests.post('{}/authorizations'.format(api_url), headers=headers, json=add_auth, auth=(user, password))
            else:
                click.echo('Invalid username or password!')
                continue
        if r.status_code == 201:
            token = r.json()['token']
        elif r.status_code == 422:
            click.echo('You already have a GitHub token for zazu in GitHub but it is not saved in the keychain! '
                       'Go to https://github.com/settings/tokens to generate a new one with "repo" scope')
            token = zazu.util.prompt('Enter new token manually')
        else:
            raise Exception('Error authenticating with GitHub, status:{} content:{}'.format(r.status_code, r.json()))
    return token


def make_gh(api_url=GITHUB_API_URL):
    """Make github object with token from the keychain."""
    import keyring  # For some reason this doesn't play nicely with threads on lazy import.
    gh = None
    token = keyring.get_password(api_url, 'token')
    if token is None:
        click.echo('No saved GitHub token found in keychain, lets add one...')
    while gh is None:
        try:
            if token is None:
                token = make_gh_token(api_url)
                gh = github.Github(token)
                keyring.set_password(api_url, 'token', token)
            else:
                gh = github.Github(token)
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
