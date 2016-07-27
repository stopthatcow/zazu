# -*- coding: utf-8 -*-
"""core functions for zazu"""
from zazu import __version__
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

import click
import jira_helper
import git_helper
import git
import teamcity_helper
import subprocess
import os
import yaml
import shutil
import cmake_helper
import tool_helper
import webbrowser
import urllib
import credential_helper
import github
import re
import jira
import concurrent.futures
import pip
import requests
import socket
import keyring
import getpass


class Config:

    def __init__(self):
        self.repo_root = None
        self.repo = None
        self._jira = None
        self._tc = None

    def jira(self):
        if self._jira is None:
            self._jira = jira_helper.make_jira()
        return self._jira


pass_config = click.make_pass_decorator(Config, ensure=True)

PROJECT_FILE_NAME = 'zazu.yaml'


def null_printer(x):
    """disregards input"""
    pass


def check_repo(config):
    """Checks that the config has a valid repo set"""
    if config.repo_root is None or config.repo is None:
        raise click.UsageError('The current working directory is not in a git repo')


class ZazuException(Exception):

    def __init___(self, error):
        Exception.__init__("Error: {}".format(error))


@click.group()
@click.version_option(version=__version__)
@pass_config
def cli(config):
    try:
        config.repo_root = git_helper.get_root_path()
        config.repo = git.Repo(config.repo_root)
    except subprocess.CalledProcessError:
        pass


@cli.command()
@click.option('--version', default='', help='version to upgrade to or empty for latest')
def upgrade(version):
    """Upgrade Zazu using pip"""
    # TODO for now hard code lily URLs, in future lean on pip.conf for this
    return pip.main(['install', '--upgrade',
                     '--trusted-host', 'pypi.lily.technology',
                     '--index-url', 'http://pypi.lily.technology:8080/simple', 'zazu{}'.format(version)])


@cli.group()
def tool():
    """Manage tools that zazu is familiar with"""
    pass


@tool.command()
@click.option('--force-reinstall', help='forces reinstallation', is_flag=True)
@click.argument('spec')
def install(spec, force_reinstall):
    """Install tools that zazu is familiar with"""
    tool_helper.install_spec(spec, force_reinstall, click.echo)


@tool.command()
@click.argument('spec')
def uninstall(spec):
    """Uninstall tools that zazu is familiar with"""
    tool_helper.uninstall_spec(spec, click.echo)


@cli.group()
@pass_config
def dev(config):
    """Create or update work items"""
    check_repo(config)


@cli.group()
@pass_config
def repo(config):
    """Manage repository"""
    check_repo(config)


@repo.group()
@pass_config
def setup(config):
    """Setup repository with services"""
    pass


ZAZU_IMAGE_URL = 'http://vignette1.wikia.nocookie.net/disney/images/c/ca/Zazu01cf.png'
ZAZU_REPO_URL = 'https://github.com/LilyRobotics/zazu'
JIRA_CREATED_BY_ZAZU = '----\n!{}|width=20! Created by [Zazu|{}]'.format(ZAZU_IMAGE_URL, ZAZU_REPO_URL)


def populate_jira_fields():
    """Prompt the user for ticket info"""
    click.echo("Making a new ticket...")
    issue_dict = {
        # TODO load project key from config
        'project': {'key': click.prompt('Enter project key', default='LC')},
        'issuetype': {'name': click.prompt('Enter an issue type', default='Task')},
        'summary': click.prompt('Enter a title'),
        'description': '{}\n\n{}'.format(click.prompt('Enter a description'), JIRA_CREATED_BY_ZAZU)
    }
    # TODO fill in repo default component
    return issue_dict


def description_to_branch(description):
    """Sanitizes a string for inclusion into branch name"""
    return description.replace(' ', '_')


def make_issue_descriptor(name):
    """Splits input into type, id and description"""
    type = None
    description = None
    if '-' not in name:
        raise click.ClickException("Branch name must be in the form PROJECT-NUMBER, type/PROJECT-NUMBER, or type/PROJECT_NUMBER_description")
    components = name.split('/')
    if len(components) == 2:
        type = components[0]
    components = components.pop().split('_', 1)
    if len(components) == 2:
        description = components[1]
    id = components[0]
    return IssueDescriptor(type, id, description)


class IssueDescriptor:
    """Info holder of type, ticket ID, and description"""

    def __init__(self, type, id, description=''):
        self.type = type
        self.id = id
        self.description = description

    def get_branch_name(self):
        sanitized_description = self.description.replace(' ', '_')
        return '{}/{}_{}'.format(self.type, self.id, sanitized_description)


def make_ticket(jira):
    """Creates a new jira ticket interactively"""
    fields = populate_jira_fields()
    issue = jira.create_issue(fields)
    # Self assign the new ticket
    jira.assign_issue(issue, issue.fields.reporter.name)
    return issue


def offer_to_stash_changes(repo):
    """Offers to stash local changes if there are any"""
    diff = repo.index.diff(None)
    status = repo.git.status('-s', '-uno')
    if len(diff) and len(status):
        click.echo(status)
        if click.confirm('Local changes detected, stash first?', default=True):
            repo.git.stash()


def verify_ticket_exists(jira, ticket_id):
    """Verify that a given ticket exists"""
    issue = jira_helper.get_issue(jira, ticket_id)
    if issue is None:
        raise click.BadParameter('no ticket named "{}"'.format(ticket_id))


@dev.command()
@click.argument('name', required=False)
@click.option('--no-verify', is_flag=True, help='Skip verification that ticket exists')
@click.option('-t', '--type', type=click.Choice(['feature', 'release', 'hotfix']), help='the ticket type to make',
              default='feature')
@pass_config
def start(config, name, no_verify, type):
    """Start a new feature, much like git-flow but with more sugar"""
    offer_to_stash_changes(config.repo)
    if name is None:
        name = str(make_ticket(config.jira()))
        click.echo('Created ticket "{}"'.format(name))
    issue = make_issue_descriptor(name)
    if not no_verify:
        verify_ticket_exists(config.jira(), issue.id)
    if issue.description is None:
        issue.description = click.prompt('Enter a short description for the branch')
    issue.type = type
    branch_name = issue.get_branch_name()
    try:
        # Check if the target branch already exists
        config.repo.git.checkout(branch_name)
        click.echo('Branch {} already exists!'.format(branch_name))
    except git.exc.GitCommandError:
        click.echo('Checking out develop...')
        config.repo.heads.develop.checkout()
        click.echo('Pulling from origin...')
        try:
            config.repo.remotes.origin.pull()
        except git.exc.GitCommandError:
            click.secho('WARNING: unable to pull from origin!', fg='red')
        click.echo('Creating new branch named "{}"...'.format(branch_name))
        config.repo.git.checkout('HEAD', b=branch_name)


def get_gh_token():
    """Make new GitHub token"""
    api_url = 'https://api.github.com'
    add_auth = {
        "scopes": [
            "repo"
        ],
        "note": "zazu for {}@{}".format(getpass.getuser(), socket.gethostname())
    }
    token = None
    while token is None:
        user = click.prompt("GitHub username", type=str)
        password = click.prompt("GitHub password", type=str, hide_input=True)
        r = requests.post('{}/authorizations'.format(api_url), json=add_auth, auth=(user, password))
        if r.status_code == 401:
            if 'Must specify two-factor authentication OTP code.' in r.json()['message']:
                headers = {'X-GitHub-OTP': click.prompt('GitHub two-factor code (6 digits)', type=str)}
                r = requests.post('{}/authorizations'.format(api_url), headers=headers, json=add_auth, auth=(user, password))
            else:
                click.echo("Invalid username or password!")
                continue
        if r.status_code == 201:
            token = r.json()['token']
        elif r.status_code == 422:
            click.echo('You already have a GitHub token for zazu in GitHub but it is not saved in the keychain! '
                       'Go to https://github.com/settings/tokens to generate a new one with "repo" scope')
            token = click.prompt('Enter new token manually')
        else:
            raise Exception("Error authenticating with GitHub, status:{} content:{}".format(r.status_code, r.json()))
    return token


def make_gh():
    token = keyring.get_password('https://api.github.com', 'token')
    if token is None:
        click.echo("No saved GitHub token found in keychain, lets add one...")
        token = get_gh_token()
        keyring.set_password('https://api.github.com', 'token', token)
    gh = github.Github(token)
    return gh


def parse_github_url(url):
    """Parses github url into organization and repo name"""
    tokens = re.split('/|:', url.replace('.git', ''))
    repo = tokens.pop()
    organization = tokens.pop()
    return organization, repo


@dev.command()
@pass_config
def status(config):
    """Get status of this branch"""
    descriptor = make_issue_descriptor(config.repo.active_branch.name)
    issue_id = descriptor.id
    if not issue_id:
        click.echo('The current branch does not contain a ticket ID')
        exit(-1)
    else:
        gh = make_gh()

        def get_issue(id):
            return config.jira().issue(id)

        def get_pulls_for_branch(branch):
            org, repo = parse_github_url(config.repo.remotes.origin.url)
            pulls = gh.get_user(org).get_repo(repo).get_pulls()
            return [p for p in pulls if p.head.ref == branch]

        # Dispatch REST calls asynchronously
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            issue_future = executor.submit(get_issue, issue_id)
            pulls_future = executor.submit(get_pulls_for_branch, config.repo.active_branch.name)

            click.echo(click.style('Ticket info:', bg='white', fg='black'))
            try:
                issue = issue_future.result()
                type = issue.fields.issuetype.name
                click.echo(click.style('    {} ({}): '.format(type, issue.fields.status.name), fg='green') + issue.fields.summary)
                click.echo(click.style('    Description: '.format(type), fg='green') + issue.fields.description.replace(JIRA_CREATED_BY_ZAZU, ''))
            except jira.exceptions.JIRAError:
                click.echo("    No JIRA ticket found")

            matches = pulls_future.result()
            click.secho('Pull request info:', bg='white', fg='black')
            click.echo('    {} matching PRs'.format(len(matches)))
            if matches:
                for p in matches:
                    click.echo(click.style('    PR Name:  ', fg='green', bold=True) + p.title)
                    click.echo(click.style('    PR State: ', fg='green', bold=True) + p.state)
                    click.echo(click.style('    PR Body:  ', fg='green', bold=True) + p.body)
                    click.echo(click.style('    PR URL:   ', fg='green', bold=True) + p.html_url)

            # TODO: build status from TC


@dev.command()
@pass_config
def review(config):
    """Create or display pull request"""
    encoded_branch = urllib.quote_plus(config.repo.active_branch.name)
    url = config.repo.remotes.origin.url
    start = 'github.com'
    if start in url:
        base_url = url[url.find(start):].replace('.git', '').replace(':', '/')
        url = 'https://{}/compare/{}?expand=1'.format(base_url, encoded_branch)
        click.echo('Opening "{}"'.format(url))
        webbrowser.open_new(url)
        # TODO: add link to jira ticket in the PR, zazu logo
        # <img src="http://vignette1.wikia.nocookie.net/disney/images/c/ca/Zazu01cf.png" alt="Zazu" width=50"/>
    else:
        raise click.UsageError("Can't open a PR for a non-github repo")


@dev.command()
@pass_config
def ticket(config):
    """Open the JIRA ticket for this feature"""
    descriptor = make_issue_descriptor(config.repo.active_branch.name)
    issue_id = descriptor.id
    if not issue_id:
        click.echo('The current branch does not contain a ticket ID')
        exit(-1)
    else:
        url = jira_helper.get_browse_url(issue_id)
        click.echo('Opening "{}"'.format(url))
        webbrowser.open_new(url)


@dev.command()
@pass_config
def builds(config):
    """Open the JIRA ticket for this feature"""
    raise NotImplementedError


# @cli.command()
# def setup():
#     """Setup pip configuration to pull packages from local pypi server"""
#     installed = False
#     try:
#         installed = pypi_helper.check_pypi_config()
#     except IOError:
#         if not click.confirm("Warning, existing pip configuration detected! Continue?", default=False):
#             return
#     if not installed:
#         pypi_helper.enforce_pypi_config()


@setup.command()
@pass_config
@click.pass_context
def all(ctx, config):
    """Setup all services"""
    ctx.forward(hooks)
    ctx.forward(ci)


@setup.command()
@pass_config
def hooks(config):
    """Setup default git hooks"""
    git_helper.install_git_hooks(config.repo_root)


@repo.command()
@pass_config
def clone(config):
    """Clone and initialize a repo"""
    raise NotImplementedError


@repo.command()
@pass_config
def init(config):
    """Initialize repo directory structure"""
    raise NotImplementedError


@repo.command()
@click.option('-r', '--remote', is_flag=True, help='Also clean up remote branches')
@pass_config
def cleanup(config, remote):
    """Clean up merged branches"""
    def filter_undeletable(branches):
        """Filters out branches that we don't want to delete"""
        return filter(lambda s: not ('master' == s or 'develop' == s or '*' in s or '-' == s), branches)

    config.repo.git.checkout('develop')
    if remote:
        config.repo.git.fetch('--prune')
        merged_remote_branches = filter_undeletable(git_helper.get_merged_branches(config.repo, 'origin/master', remote=True))
        if merged_remote_branches:
            click.echo('The following remote branches will be deleted:')
            for b in merged_remote_branches:
                click.echo('    - {}'.format(b))
            if click.confirm('Proceed?'):
                for b in merged_remote_branches:
                    click.echo('Deleting {}'.format(b))
                    config.repo.git.push('--delete', 'origin', b.replace('origin/', ''))
    merged_branches = filter_undeletable(git_helper.get_merged_branches(config.repo, 'origin/master'))
    if merged_branches:
        click.echo('The following local branches will be deleted:')
        for b in merged_branches:
            click.echo('    - {}'.format(b))
        if click.confirm('Proceed?'):
            for b in merged_branches:
                click.echo('Deleting {}'.format(b))
                config.repo.git.branch('-d', b)


def load_project_file(path):
    """Load a project yaml file"""
    with open(path) as f:
        return yaml.load(f)


@setup.command()
@pass_config
def ci(config):
    """Setup TeamCity configurations based on a zazu.yaml file"""
    address = 'teamcity.lily.technology'
    port = 8111
    check_repo(config)
    config.tc = teamcity_helper.make_tc(address, port)
    try:
        project_config = load_project_file(os.path.join(config.repo_root, PROJECT_FILE_NAME))
        if click.confirm("Post build configuration to TeamCity?"):
            components = project_config['components']
            for c in components:
                component = ComponentConfiguration(c)
                teamcity_helper.setup(config.tc, component, config.repo_root)
    except IOError:
        raise ZazuException("No {} file found in {}".format(project_file_name, config.repo_root))


class ComponentConfiguration:

    def __init__(self, component):
        self._name = component['name']
        self._description = component.get('description', '')
        self._goals = {}
        for g in component['goals']:
            self._goals[g['name']] = BuildGoal(g)

    def get_spec(self, goal, arch, type):
        try:
            build_goal = self._goals[goal]
            ret = build_goal.get_build(arch)
            if type is not None:
                ret._build_type = type
        except KeyError:
            ret = BuildSpec()
        return ret

    def description(self):
        return self._description

    def name(self):
        return self._name

    def goals(self):
        return self._goals


class BuildGoal:

    def __init__(self, goal):
        self._name = goal.get('name', '')
        self._description = goal.get('description', '')
        self._build_type = goal.get('buildType', None)
        self._build_vars = goal.get('buildVars', {})
        self._requires = goal.get('requires', {})
        self._builds = {}
        self._default_spec = BuildSpec(self._build_type, self._build_vars, self._requires, self._description)
        for b in goal['builds']:
            vars = b.get('buildVars', self._build_vars)
            type = b.get('buildType', self._build_type)
            requires = b.get('requires', {})
            requires.update(self._requires)
            description = b.get('description', '')
            arch = b['arch']
            script = b.get('script', None)
            self._builds[arch] = BuildSpec(type, vars, requires, description, arch, script=script)

    def description(self):
        return self._description

    def name(self):
        return self._name

    def builds(self):
        return self._builds

    def get_build(self, arch):
        return self._builds.get(arch, self._default_spec)


class BuildSpec:

    def __init__(self, type='release', vars={}, requires={}, description='', arch='', script=None):
        self._build_type = type
        self._build_vars = vars
        self._build_requires = requires
        self._build_description = description
        self._build_arch = arch
        self._build_script = script

    def build_type(self):
        return self._build_type

    def build_vars(self):
        return self._build_vars

    def build_requires(self):
        return self._build_requires

    def build_description(self):
        return self._build_description

    def build_arch(self):
        return self._build_arch

    def build_script(self):
        return self._build_script


def cmake_build(repo_root, arch, type, goal, verbose, vars):
    """Build using cmake"""
    build_dir = os.path.join(repo_root, 'build', '{}-{}'.format(arch, type))
    ret = 0
    try:
        os.makedirs(build_dir)
    except OSError:
        pass
    if 'distclean' in goal:
        shutil.rmtree(build_dir)
    else:
        echo = null_printer
        if verbose:
            echo = click.echo
        ret = cmake_helper.configure(repo_root, build_dir, arch, type, vars, echo=echo)
        if ret:
            raise ZazuException("Error configuring with cmake")
        ret = cmake_helper.build(build_dir, type, goal, verbose)
        if ret:
            raise ZazuException("Error building with cmake")
    return ret


@cli.command()
@pass_config
@click.option('-a', '--arch', default='local', help='the desired architecture to build for')
@click.option('-t', '--type', type=click.Choice(cmake_helper.build_types), help='defaults to what is specified in the zazu.yaml file, or release if unspecified there')
@click.option('-v', '--verbose', is_flag=True, help='generates verbose output from the build')
@click.argument('goal')
def build(config, arch, type, verbose, goal):
    """Build project targets, the GOAL argument is the desired make target,
     use distclean to clean whole build folder"""
    # Run the supplied build command if there is one, otherwise assume cmake
    # Parse file to find requirements then check that they exist, then build
    project_config = load_project_file(os.path.join(config.repo_root, PROJECT_FILE_NAME))
    component = ComponentConfiguration(project_config['components'][0])
    spec = component.get_spec(goal, arch, type)
    requirements = spec.build_requires().get('zazu', [])
    for req in requirements:
        if verbose:
            tool_helper.install_spec(req, echo=click.echo)
        else:
            tool_helper.install_spec(req)
    ret = 0
    if spec.build_script() is None:
        ret = cmake_build(config.repo_root, arch, spec.build_type(), goal, verbose, spec.build_vars())
    else:
        for s in spec.build_script():
            if verbose:
                click.echo(str(s))
            ret = subprocess.call(str(s), shell=True)
            if ret:
                click.echo("Error {} exited with code {}".format(str(s), ret))
                break
    return ret
