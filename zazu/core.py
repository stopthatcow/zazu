# -*- coding: utf-8 -*-
"""core functions for zazu"""

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

import click
import jira_helper
import pypi_helper
import git_helper
import git
import teamcity_helper
import subprocess
import os
import yaml
import shutil
import cmake_helper
import tool_helper
import sys
import webbrowser
import urllib
import credential_helper
import github

class Config:
    def __init__(self):
        self.address=''
        self.repo_root = None

pass_config = click.make_pass_decorator(Config, ensure=True)

PROJECT_FILE_NAME = 'zazu.yaml'

@click.group()
@pass_config
@click.pass_context
def cli(ctx, config):
    try:
        config.repo_root = git_helper.get_root_path()
        config.repo = git.Repo(config.repo_root)
    except subprocess.CalledProcessError:
        ctx.fail("Current directory is not a git repo")


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
def feature():
    """Create or update work items"""
    pass


@feature.command()
@click.argument('name')
@pass_config
def start(config, name):
    """Start a new feature, much like git-flow but with more sugar"""
    if name is None:
        # TODO: interactively make new issue
        click.echo('FIXME here we should interactively make new issue, until then supply a ticket number'.format(spec))
        sys.exit(-1)
        return
    diff = config.repo.index.diff(None)
    if len(diff):
        click.echo(config.repo.git.status('-s', '-uno'))
        if click.confirm('Local changes detected, stash first?', default=True):
            config.repo.git.stash()
    branch_name = 'feature/' + name
    try:
        # Check if the target branch already exists
        config.repo.git.checkout(branch_name)
        click.echo('Branch {} already exists!'.format(branch_name))
    except git.exc.GitCommandError:
        click.echo('Checking out develop...')
        config.repo.heads.develop.checkout()
        click.echo('Pulling from origin...')
        config.repo.remotes.origin.pull()
        click.echo('Creating new branch named "{}"...'.format(branch_name))
        config.repo.git.checkout('HEAD', b=branch_name)


def make_gh():
    use_saved_credentials = True
    while True:
        user, password = credential_helper.get_user_pass_credentials('GitHub', use_saved_credentials)
        gh = github.Github(user, password)
        try:
            # TODO find a fast way to check credentials
            # gh.get_user().name
            break
        except github.GithubException:
            click.echo("incorrect username or password!")
            use_saved_credentials = False
    return gh


@feature.command()
@pass_config
def status(config):
    """Get status of this feature branch"""
    gh = make_gh()
    pulls = gh.get_user('LilyRobotics').get_repo('calibration').get_pulls()
    for p in pulls:
        if p.head.ref == config.repo.active_branch.name:
            click.echo(click.style('Name:  ', fg='green', bold=True) + p.title)
            click.echo(click.style('State: ', fg='green', bold=True) + p.state)
            click.echo(click.style('Body:\n', fg='green', bold=True) + p.body)
            click.echo(click.style('URL: ', fg='green', bold=True) + p.html_url)
            break


@feature.command()
@pass_config
def pr(config):
    """Create a pull request for this feature branch"""
    encoded_branch = urllib.quote_plus(config.repo.active_branch.name)
    url = config.repo.remotes.origin.url
    start = 'github.com'
    if start in url:
        project = url[url.find(start):].replace('.git','')
        webbrowser.open_new('https://{}/compare/{}?expand=1'.format(project, encoded_branch))
    else:
        click.echo("Can't open a PR for a non-github repo")


@cli.group()
@pass_config
def repo(config):
    """Configure repos"""
    pass


@cli.command()
def setup():
    """Setup pip configuration to pull packages from local pypi server"""
    installed = False
    try:
        installed = pypi_helper.check_pypi_config()
    except IOError:
        if not click.confirm("Warning, existing pip configuration detected! Continue?", default=False):
            return
    if not installed:
        pypi_helper.enforce_pypi_config()


@repo.command()
@pass_config
def setup(config):
    """Setup default git hooks"""
    git_helper.install_git_hooks(config.repo_root)


@cli.group()
@click.option('-a', '--address', default='teamcity')
@click.option('-p', '--port', default=8111)
@pass_config
def tc(config, address, port):
    """Manage/setup TeamCity"""
    config.tc = teamcity_helper.make_tc(address, port)

    pass


def load_project_file(path):
    """Load a project yaml file"""
    with open(path) as f:
        return yaml.load(f)


@tc.command()
@pass_config
@click.pass_context
def setup(ctx, config):
    """Create project TeamCity configurations based on a config file"""
    try:
        project_config = load_project_file(os.path.join(config.repo_root, PROJECT_FILE_NAME))
        components = project_config['components']
        for c in components:
            component = ComponentConfiguration(c)
            teamcity_helper.setup(config.tc, component, config.repo_root)
    except IOError:
        ctx.fail("No {} file found in {}".format(project_file_name, config.repo_root))


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
            self._builds[arch] = BuildSpec(type, vars, requires, description, arch)

    def description(self):
        return self._description

    def name(self):
        return self._name

    def builds(self):
        return self._builds

    def get_build(self, arch):
        return self._builds.get(arch, self._default_spec)


class BuildSpec:
    def __init__(self, type='release', vars={}, requires={}, description='', arch=''):
        self._build_type = type
        self._build_vars = vars
        self._build_requires = requires
        self._build_description = description
        self._build_arch = arch

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


@cli.command()
@pass_config
@click.option('-a', '--arch', default='local', help='the desired architecture to build for')
@click.option('-t', '--type', type=click.Choice(cmake_helper.build_types), help='defaults to what is specified in the zazu.yaml file, or release if unspecified there')
@click.option('-v', '--verbose', is_flag=True, help='generates verbose output from the build')
@click.argument('goal')
@click.pass_context
def build(ctx, config, arch, type, verbose, goal):
    """CI entry point to build project targets, the GOAL argument is the desired make target,
     use distclean to clean whole build folder"""
    # TODO Run the supplied build command
    # For now assume cmake
    r = 0
    build_dir = os.path.join(config.repo_root, 'build', '{}-{}'.format(arch, type))
    try:
        os.makedirs(build_dir)
    except OSError:
        pass
    if 'distclean' in goal:
        shutil.rmtree(build_dir)
    else:
        # Parse file to find requirements then check that they exist, then build
        project_config = load_project_file(os.path.join(config.repo_root, PROJECT_FILE_NAME))
        component = ComponentConfiguration(project_config['components'][0])
        spec = component.get_spec(goal, arch, type)
        requirements = spec.build_requires().get('zazu', [])
        for r in requirements:
            tool_helper.install_spec(r)
        r = cmake_helper.configure(config.repo_root, build_dir, arch, spec.build_type(), spec.build_vars())
        if r:
            click.echo("Error configuring with cmake")
            ctx.exit(r)
        r = cmake_helper.build(build_dir, type, goal, verbose)
        if r:
            click.echo("Error building with cmake")
            ctx.exit(r)
    return r
