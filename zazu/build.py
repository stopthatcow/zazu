# -*- coding: utf-8 -*-
"""build command for zazu"""
import click
import shutil
import subprocess
import semantic_version
import os
import zazu.tool.tool_helper
import zazu.cmake_helper
import zazu.config


class ComponentConfiguration(object):
    """Stores a configuration for a single component"""

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
            ret = BuildSpec(goal)
        return ret

    def description(self):
        return self._description

    def name(self):
        return self._name

    def goals(self):
        return self._goals


class BuildGoal(object):
    """Stores a configuration for a single build goal with one or more architectures"""

    def __init__(self, goal):
        self._name = goal.get('name', '')
        self._description = goal.get('description', '')
        self._build_type = goal.get('buildType', None)
        self._build_vars = goal.get('buildVars', {})
        self._build_goal = goal.get('buildGoal', self._name)
        self._requires = goal.get('requires', {})
        self._builds = {}
        self._default_spec = BuildSpec(self._build_goal, self._build_type, self._build_vars, self._requires, self._description)
        for b in goal['builds']:
            vars = b.get('buildVars', self._build_vars)
            type = b.get('buildType', self._build_type)
            build_goal = b.get('buildGoal', self._build_goal)
            requires = b.get('requires', {})
            requires.update(self._requires)
            description = b.get('description', '')
            arch = b['arch']
            script = b.get('script', None)
            self._builds[arch] = BuildSpec(build_goal, type, vars, requires, description, arch, script=script)

    def description(self):
        return self._description

    def name(self):
        return self._name

    def goal(self):
        return self._build_goal

    def builds(self):
        return self._builds

    def get_build(self, arch):
        return self._builds.get(arch, self._default_spec)


class BuildSpec(object):

    def __init__(self, goal, type='minSizeRel', vars={}, requires={}, description='', arch='', script=None):
        self._build_goal = goal
        self._build_type = type
        self._build_vars = vars
        self._build_requires = requires
        self._build_description = description
        self._build_arch = arch
        self._build_script = script

    def build_type(self):
        return self._build_type

    def build_goal(self):
        return self._build_goal

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


def cmake_build(repo_root, arch, type, goal, verbose, vars, version):
    """Build using cmake"""
    if arch not in zazu.cmake_helper.known_arches():
        raise click.BadParameter("Arch not recognized, choose from:\n    - {}".format('\n    - '.join(zazu.cmake_helper.known_arches())))

    build_dir = os.path.join(repo_root, 'build', '{}-{}'.format(arch, type))
    ret = 0
    try:
        os.makedirs(build_dir)
    except OSError:
        pass
    if 'distclean' in goal:
        shutil.rmtree(build_dir)
    else:
        ret = zazu.cmake_helper.configure(repo_root, build_dir, arch, type, vars, version, click.echo if verbose else lambda x: x)
        if ret:
            raise click.ClickException("Error configuring with cmake")
        ret = zazu.cmake_helper.build(build_dir, type, goal, verbose)
        if ret:
            raise click.ClickException("Error building with cmake")
    return ret


def tag_to_version(tag):
    """Converts a git tag into a semantic version string.
     i.e. R4.1 becomes 4.1.0. A leading 'r' or 'v' is optional on the tag"""
    components = []
    if tag is not None:
        if tag.lower().startswith('r') or tag.lower().startswith('v'):
            tag = tag[1:]
        components = tag.split('.')
    major = '0'
    minor = '0'
    patch = '0'
    try:
        major = components[0]
        minor = components[1]
        patch = components[2]
    except IndexError:
        pass

    return '.'.join([major, minor, patch])


def make_semver(repo_root, build_number):
    """Parses SCM info and creates a semantic version"""
    branch_name, sha, last_tag, commits_past_tag = parse_describe(repo_root)
    return make_version_number(branch_name, build_number, last_tag, commits_past_tag, sha)


def parse_describe(repo_root):
    """Parses the results of git describe into branch name, sha, last tag, and number of commits since the tag"""
    stdout = subprocess.check_output(['git', 'describe', '--dirty=.dirty', '--always'], cwd=repo_root)
    components = stdout.strip().split('-')
    sha = None
    commits_past = 0
    last_tag = None
    try:
        sha = components.pop()
        commits_past = components.pop()
        last_tag = components.pop()
    except IndexError:
        pass
    branch_name = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_root).rstrip()
    return branch_name, sha, last_tag, commits_past


def make_version_number(branch_name, build_number, last_tag, commits_past_tag, sha):
    """Converts repo metadata and build version into a semantic version"""
    branch_name = branch_name.replace('/', '.')
    branch_name = branch_name.replace('-', '.')
    branch_name = branch_name.replace('_', '.')
    build_info = ['sha', sha, 'build', str(build_number), 'branch', branch_name]
    prerelease = []

    if last_tag is not None and commits_past_tag == 0:
        version = tag_to_version(last_tag)
    elif branch_name.startswith('release/') or branch_name.startswith('hotfix/'):
        version = tag_to_version(branch_name.split('/')[1:])
        prerelease = [str(build_number)]
    else:
        version = '0.0.0'
        prerelease = [str(build_number)]
    semver = semantic_version.Version(version)
    semver.prerelease = prerelease
    semver.build = build_info

    return semver


def populate_version_environ_vars(version):
    """Populates environment variables from a semantic version"""
    os.environ["ZAZU_BUILD_VERSION"] = str(version)
    os.environ["ZAZU_BUILD_VERSION_MAJOR"] = str(version.major)
    os.environ["ZAZU_BUILD_VERSION_MINOR"] = str(version.minor)
    os.environ["ZAZU_BUILD_VERSION_PATCH"] = str(version.patch)


def install_requirements(requirements, verbose):
    """Installs the requirements using the zazu tool manager"""
    for req in requirements:
        if verbose:
            zazu.tool.tool_helper.install_spec(req, echo=click.echo)
        else:
            zazu.tool.tool_helper.install_spec(req)


def script_build(repo_root, spec, verbose):
    """Build using a provided shell script"""
    for s in spec.build_script():
        if verbose:
            click.echo(str(s))
        ret = subprocess.call(str(s), shell=True, cwd=repo_root)
        if ret:
            raise click.ClickException("{} exited with code {}".format(str(s), ret))


@click.command()
@click.pass_context
@click.option('-a', '--arch', default='local', help='the desired architecture to build for')
@click.option('-t', '--type', type=click.Choice(zazu.cmake_helper.build_types),
              help='defaults to what is specified in the {} file, or release if unspecified there'.format(zazu.config.PROJECT_FILE_NAME))
@click.option('-n', '--build_num', help='build number', default=os.environ.get('BUILD_NUMBER', 0))
@click.option('-v', '--verbose', is_flag=True, help='generates verbose output from the build')
@click.argument('goal')
def build(ctx, arch, type, build_num, verbose, goal):
    """Build project targets, the GOAL argument is the configuration name from zazu.yaml file or desired make target,
     use distclean to clean whole build folder"""
    # Run the supplied build script if there is one, otherwise assume cmake
    # Parse file to find requirements then check that they exist, then build
    project_config = ctx.obj.project_config()
    component = ComponentConfiguration(project_config['components'][0])
    spec = component.get_spec(goal, arch, type)
    requirements = spec.build_requires().get('zazu', [])
    install_requirements(requirements, verbose)
    os.environ["ZAZU_BUILD_NUMBER"] = str(build_num)
    os.environ["ZAZU_TOOL_DIR"] = os.path.expanduser('~/.zazu/tools')
    version = make_semver(ctx.obj.repo_root, build_num)
    populate_version_environ_vars(version)
    if spec.build_script() is None:
        cmake_build(ctx.obj.repo_root, arch, spec.build_type(), spec.build_goal(), verbose, spec.build_vars(), version)
    else:
        script_build(ctx.obj.repo_root, spec, verbose)
