# -*- coding: utf-8 -*-
"""build command for zazu"""

import zazu.cmake_helper
import zazu.config
import zazu.tool.tool_helper
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'os',
    'shutil',
    'semantic_version',
    'subprocess'
])


__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


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
        self._build_type = goal.get('buildType', 'minSizeRel')
        self._build_vars = goal.get('buildVars', {})
        self._build_goal = goal.get('buildGoal', self._name)
        self._requires = goal.get('requires', {})
        self._artifacts = goal.get('artifacts', [])
        self._builds = {}
        for b in goal['builds']:
            vars = b.get('buildVars', self._build_vars)
            type = b.get('buildType', self._build_type)
            build_goal = b.get('buildGoal', self._build_goal)
            requires = b.get('requires', {})
            requires.update(self._requires)
            description = b.get('description', '')
            arch = b['arch']
            script = b.get('script', None)
            artifacts = b.get('artifacts', self._artifacts)
            self._builds[arch] = BuildSpec(goal=build_goal,
                                           type=type,
                                           vars=vars,
                                           requires=requires,
                                           description=description,
                                           arch=arch,
                                           script=script,
                                           artifacts=artifacts)

    def description(self):
        return self._description

    def name(self):
        return self._name

    def goal(self):
        return self._build_goal

    def builds(self):
        return self._builds

    def get_build(self, arch):
        if arch is None:
            if len(self._builds) == 1:
                only_arch = self._builds.keys()[0]
                click.echo("No arch specified, but there is only one ({})".format(only_arch))
                return self._builds[only_arch]
            else:
                raise click.ClickException("No arch specified, but there are multiple arches available")
        return self._builds[arch]


class BuildSpec(object):

    def __init__(self, goal, type='minSizeRel', vars={}, requires={}, description='', arch='', script=None, artifacts=[]):
        self._build_goal = goal
        self._build_type = type
        self._build_vars = vars
        self._build_requires = requires
        self._build_description = description
        self._build_arch = arch
        self._build_script = script
        self._build_artifacts = artifacts

    def build_type(self):
        return self._build_type

    def build_artifacts(self):
        return self._build_artifacts

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


def cmake_build(repo_root, arch, type, goal, verbose, vars):
    """Build using cmake"""
    if arch not in zazu.cmake_helper.known_arches():
        raise click.BadParameter('Arch "{}" not recognized, choose from:\n'.format(arch, zazu.util.pprint_list(zazu.cmake_helper.known_arches())))

    build_dir = os.path.join(repo_root, 'build', '{}-{}'.format(arch, type))
    ret = 0
    try:
        os.makedirs(build_dir)
    except OSError:
        pass
    ret = zazu.cmake_helper.configure(repo_root, build_dir, arch, type, vars, click.echo if verbose else lambda x: x)
    if ret:
        raise click.ClickException('Error configuring with cmake')
    ret = zazu.cmake_helper.build(build_dir, arch, type, goal, verbose)
    if ret:
        raise click.ClickException('Error building with cmake')
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
    stdout = subprocess.check_output(['git', 'describe', '--dirty=.dirty', '--always', '--long'], cwd=repo_root)
    components = stdout.strip().split('-')
    sha = None
    commits_past = 0
    last_tag = None
    try:
        sha = components.pop()
        sha = sha.replace('.dirty', '-dirty')
        commits_past = int(components.pop())
        last_tag = '-'.join(components)
    except IndexError:
        pass
    branch_name = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_root).rstrip()
    return branch_name, sha, last_tag, commits_past


def sanitize_branch_name(branch_name):
    """replaces punctuation that cannot be in semantic version from a branch name and replaces them with dashes"""
    return branch_name.replace('/', '-').replace('_', '-')


def make_version_number(branch_name, build_number, last_tag, commits_past_tag, sha):
    """Converts repo metadata and build version into a semantic version"""
    branch_name_sanitized = sanitize_branch_name(branch_name)
    build_info = ['sha', sha, 'build', str(build_number), 'branch', branch_name_sanitized]
    prerelease = []
    if last_tag is not None and commits_past_tag == 0:
        version = tag_to_version(last_tag)
    elif branch_name.startswith('release/') or branch_name.startswith('hotfix/'):
        version = tag_to_version(branch_name.split('/', 1)[1])
        prerelease = [str(build_number)]
    else:
        version = '0.0.0'
        prerelease = [str(build_number)]
    semver = semantic_version.Version(version)
    semver.prerelease = prerelease
    semver.build = build_info

    return semver


def pep440_from_semver(semver):
    # Convert semantic version to PEP440 compliant version
    segment = ''
    if semver.prerelease:
        segment = '.dev{}'.format('.'.join(semver.prerelease))
    local_version = '.'.join(semver.build)
    local_version = local_version.replace('-', '.')
    version_str = '{}.{}.{}{}'.format(semver.major, semver.minor, semver.patch, segment)
    # Include the local version if we are not a true release
    if local_version and semver.prerelease:
        version_str = '{}+{}'.format(version_str, local_version)
    return version_str


def install_requirements(requirements, verbose):
    """Installs the requirements using the zazu tool manager"""
    for req in requirements:
        zazu.tool.tool_helper.install_spec(req, echo=click.echo if verbose else lambda x: x)


def script_build(repo_root, spec, build_args, verbose):
    """Build using a provided shell script"""
    env = os.environ
    env.update(build_args)
    for s in spec.build_script():
        if verbose:
            click.echo(str(s))
        ret = subprocess.call(str(s), shell=True, cwd=repo_root, env=env)
        if ret:
            raise click.ClickException("{} exited with code {}".format(str(s), ret))


def parse_key_value_pairs(arg_string):
    """Parses a argument string in the form x=y j=k and returns a dictionary of the key value pairs"""
    try:
        return {key: value for (key, value) in [tuple(str(arg).split('=', 1)) for arg in arg_string]}
    except ValueError:
        raise click.ClickException("argument string must be in the form x=y")


def add_version_args(repo_root, build_num, args):
    """Adds version strings and build number arguments to args"""
    try:
        semver = semantic_version.Version(args['ZAZU_BUILD_VERSION'])
    except KeyError:
        semver = make_semver(repo_root, build_num)
        args['ZAZU_BUILD_VERSION'] = str(semver)
    args["ZAZU_BUILD_NUMBER"] = str(build_num)
    args['ZAZU_BUILD_VERSION_PEP440'] = pep440_from_semver(semver)


@click.command()
@click.pass_context
@click.option('-a', '--arch', help='the desired architecture to build for')
@click.option('-t', '--type', type=click.Choice(zazu.cmake_helper.build_types),
              help='defaults to what is specified in the config file, or release if unspecified there')
@click.option('-n', '--build_num', help='build number', default=os.environ.get('BUILD_NUMBER', 0))
@click.option('-v', '--verbose', is_flag=True, help='generates verbose output from the build')
@click.argument('goal')
@click.argument('extra_args_str', nargs=-1)
def build(ctx, arch, type, build_num, verbose, goal, extra_args_str):
    """Build project targets, the GOAL argument is the configuration name from zazu.yaml file or desired make target"""
    # Run the supplied build script if there is one, otherwise assume cmake
    # Parse file to find requirements then check that they exist, then build
    project_config = ctx.obj.project_config()
    component = ComponentConfiguration(project_config['components'][0])
    spec = component.get_spec(goal, arch, type)
    requirements = spec.build_requires().get('zazu', [])
    install_requirements(requirements, verbose)
    build_args = {"ZAZU_TOOL_DIR": zazu.tool.tool_helper.package_path}
    extra_args = parse_key_value_pairs(extra_args_str)
    build_args.update(spec.build_vars())
    build_args.update(extra_args)
    add_version_args(ctx.obj.repo_root, build_num, build_args)
    if spec.build_script() is None:
        cmake_build(ctx.obj.repo_root, spec.build_arch(), spec.build_type(), spec.build_goal(), verbose, build_args)
    else:
        script_build(ctx.obj.repo_root, spec, build_args, verbose)
    try:
        ctx.obj.build_server().publish_artifacts(spec.build_artifacts())
    except click.ClickException:
        pass
