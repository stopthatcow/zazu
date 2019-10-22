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
    'zazu.keychain',
    'zazu.util',
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


GITHUB_API_URL = 'https://api.github.com'


def get_api_url(api_url=None):
    return zazu.util.base_url(GITHUB_API_URL if api_url is None else api_url)


def make_gh_token(api_url=None):
    """Make new GitHub token."""
    api_url = get_api_url(api_url)
    add_auth = {
        'scopes': [
            'repo'
        ],
        'note': 'zazu for {}@{}'.format(getpass.getuser(), socket.gethostname())
    }
    interface = zazu.keychain.CredentialInterface('github', api_url, ['username'], ['password'])
    token = None
    while token is None and click.confirm('Create a new GitHub API token for zazu?'):
        interface.set_interactive()
        user_pass = (interface['username'], interface['password'])
        r = requests.post('{}/authorizations'.format(api_url), json=add_auth, auth=user_pass)
        if r.status_code == 401:
            if 'Must specify two-factor authentication OTP code.' in r.json()['message']:
                headers = {'X-GitHub-OTP': click.prompt('GitHub two-factor code (6 digits)', type=str)}
                r = requests.post('{}/authorizations'.format(api_url), headers=headers, json=add_auth, auth=user_pass)
            else:
                click.echo('Invalid username or password!')
                continue
        if r.status_code == 201:
            return r.json()['token']
        elif r.status_code == 422:
            click.echo('You already have a token for zazu in GitHub but it is not saved in the keychain!')
        else:
            click.echo('Error authenticating with GitHub, status:{} content:{}'.format(r.status_code, r.json()))
        break
    click.echo('Go to GitHub and generate a new token with "repo" scope')
    return click.prompt('Enter token', type=str)


def github_from_credentials(credentials):
    return github.Github(base_url=credentials.url(), login_or_token=credentials['token'])


def validate_credentials(gh):
    try:
        gh.get_user().name  # Hit the API to validate the credentials.
        return True
    except github.BadCredentialsException:
        pass
    return False


def make_and_validate_github_from_credentials(credentials):
    return validate_credentials(github_from_credentials(credentials))


def token_credential_interface(api_url=None):
    """"""
    return zazu.keychain.CredentialInterface('github', get_api_url(api_url), ['token'],
                                             validator_callback=make_and_validate_github_from_credentials)


def make_gh(api_url=None):
    """Make github object with token from the keychain."""
    gh = None
    token_interface = token_credential_interface(api_url)
    token_found = token_interface.load()
    if not token_found:
        click.echo('No saved GitHub token found in keychain, lets add one...')
    while gh is None:
        if not token_found:
            token_interface['token'] = make_gh_token(api_url)
            gh = github_from_credentials(token_interface)
            if not validate_credentials(gh):
                click.echo("GitHub token rejected, you will need to create a new token.")
                token_found = False
            else:
                token_interface.save()
                return gh
        else:
            gh = github_from_credentials(token_interface)
    return gh


def parse_github_url(url):
    """Parse github url into organization and repo name."""
    tokens = re.split('/|:', url.replace('.git', ''))
    repo = tokens.pop()
    organization = tokens.pop()
    return organization, repo
