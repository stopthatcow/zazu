# -*- coding: utf-8 -*-
"""Config classes and methods for zazu."""
import zazu.code_reviewer
import zazu.git_helper
import zazu.issue_tracker
import zazu.scm_host
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'dict_recursive_update',
    'git',
    'os',
    'ruamel.yaml',
    'straight.plugin',
    'subprocess',
    'sys'
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'

PROJECT_FILE_NAMES = ['zazu.yaml', '.zazu.yaml']


class PluginFactory(object):
    """A genetic plugin factory that uses the type field of the config to create the appropriate class."""

    def __init__(self, name, subclass):
        """Constructor.

        Args:
            name (str): the name of the plugin type.
            subclass (type): subclasses of this type will be loaded as potential plugins.

        """
        self._subclass = subclass
        self._name = name

    def from_config(self, config):
        """Make and initialize a plugin object from a config."""
        plugins = straight.plugin.load('zazu.plugins', subclasses=self._subclass)
        known_types = {p.type().lower(): p.from_config for p in plugins}
        if 'type' in config:
            type = config['type']
            if type in known_types:
                return known_types[type](config)
            else:
                raise click.ClickException('{} is not a known {}, please choose from {}'.format(type,
                                                                                                self._name,
                                                                                                sorted(known_types.keys())))
        else:
            raise click.ClickException('{} config requires a "type" field'.format(self._name))


issue_tracker_factory = PluginFactory('issueTracker', zazu.issue_tracker.IssueTracker)
code_reviewer_factory = PluginFactory('codeReviewer', zazu.code_reviewer.CodeReviewer)


def scm_host_factory(user_config, config):
    """Make and initialize the ScmHosts from the config."""
    hosts = {}
    default_host = ''
    plugins = straight.plugin.load('zazu.plugins', subclasses=zazu.scm_host.ScmHost)
    known_types = {p.type(): p for p in plugins}
    for name, value in config.iteritems():
        # The "default" host is unique.
        if name == 'default':
            if isinstance(value, dict):
                default_host = 'default'
            else:
                default_host = value
                continue
        if 'type' in value:
            type = value['type']
            if type in known_types:
                hosts[name] = known_types[type].from_config(value)
            else:
                raise click.ClickException('{} is not a known ScmHost, please choose from {}'.format(type,
                                                                                                     sorted(known_types.keys())))
        else:
            raise click.ClickException('scmHost config requires a "type" field')

    if default_host:
        if default_host not in hosts:
            raise click.ClickException('default scmHost \'{}\' not found'.format(default_host))
    elif len(hosts) == 1:  # Only 1 known host makes it the default.
        default_host = hosts.keys()[0]

    return hosts, default_host


def styler_factory(config):
    """Make and initialize the Stylers from the config."""
    stylers = []
    plugins = straight.plugin.load('zazu.plugins', subclasses=zazu.styler.Styler)
    known_types = {p.type(): p for p in plugins}
    for entry in config:
        excludes = entry.get('exclude', [])
        for styler in entry['stylers']:
            name = styler['type']
            if name in known_types:
                includes = entry.get('include', known_types[name].default_extensions())
                stylers.append(known_types[name].from_config(styler, excludes, includes))
            else:
                raise click.ClickException('{} is not a known styler, please choose from {}'.format(name,
                                                                                                    sorted(known_types.keys())))
    return stylers


def path_gen(search_paths, file_names):
    """Generate full paths given a list of directories and list of file names."""
    for p in search_paths:
        for f in file_names:
            yield os.path.join(p, f)


def get_line(file_path, line_number):
    """Return line number in file."""
    with open(file_path, 'r') as fp:
        for i, line in enumerate(fp):
            if i == line_number:
                return line


def make_col_indicator(index):
    """Return a carrot indicator at index."""
    return '{}^'.format(' ' * index)


def find_file(search_paths, file_names):
    """Search search_paths for file_names."""
    searched = path_gen(search_paths, file_names)
    for file_name in searched:
        try:
            with open(file_name, 'r') as f:
                return file_name
        except IOError:
            pass
    return None


def load_yaml_file(filepath):
    """Load a yaml file."""
    with open(filepath, 'r') as f:
        try:
            yaml = ruamel.yaml.YAML()
            config = yaml.load(f)
            if config is None:
                config = {}
        except ruamel.yaml.YAMLError as e:
            error_string = ''
            if hasattr(e, 'problem_mark'):
                error_line = get_line(filepath, e.problem_mark.line)
                col_indicator = make_col_indicator(e.problem_mark.column)
                error_string = "invalid_syntax: '{}'\n" \
                               '                 {}'.format(error_line, col_indicator)
            raise click.ClickException('unable to parse file \'{}\'\n{}'.format(filepath, error_string))
        return config


def find_and_load_yaml_file(search_paths, file_names):
    """Find and load a yaml file."""
    filepath = find_file(search_paths, file_names)
    if filepath is not None:
        return load_yaml_file(filepath)
    searched = path_gen(search_paths, file_names)
    raise click.ClickException('no yaml file found, searched:{}'.format(zazu.util.pprint_list(searched)))


def user_config_filepath():
    """User configuration file path."""
    return os.path.join(os.path.expanduser('~'), '.zazuconfig.yaml')


class ConfigFile(object):
    """Holds a parsed config file and can write changes to disk."""

    def __init__(self, path):
        """Store path and read the contents from disk if it exists."""
        self._path = path
        self.dict = {}
        if self.exists():
            self.read()

    def exists(self):
        """Return True if the path exists."""
        return os.path.isfile(self._path)

    def read(self):
        """Read config file from disk."""
        self.dict = load_yaml_file(self._path)

    def write(self):
        """Write config file to disk."""
        yaml = ruamel.yaml.YAML()
        with open(self._path, 'w') as f:
            yaml.dump(self.dict, f)


class Config(object):
    """Hold all zazu configuration info."""

    def __init__(self, repo_root=None):
        """Constructor, doesn't parse configuration or require repo to be valid."""
        if repo_root is None:
            repo_root = zazu.git_helper.get_repo_root(os.getcwd())
        self.repo_root = repo_root
        if self.repo_root is not None:
            try:
                self.repo = git.Repo(self.repo_root)
            except git.InvalidGitRepositoryError:
                self.repo = None
        self._issue_tracker = None
        self._code_reviewer = None
        self._scm_hosts = None
        self._default_scm_host = None
        self._project_config = None
        self._user_config = None
        self._stylers = None

    def issue_tracker(self):
        """Lazily create a IssueTracker object."""
        if self._issue_tracker is None:
            self._issue_tracker = issue_tracker_factory.from_config(self.issue_tracker_config())
        return self._issue_tracker

    def issue_tracker_config(self):
        """Return the issue tracker configuration if one exists.

        Raises:
            click.ClickException: if no issue tracker configuration is present.

        """
        try:
            return self.project_config()['issueTracker']
        except KeyError:
            raise click.ClickException('no issueTracker config found')

    def code_reviewer_config(self):
        """Return the code reviewer configuration if one exists.

        Raises:
           click.ClickException: if no code review configuration is present.

        """
        try:
            return self.project_config()['codeReviewer']
        except KeyError:
            raise click.ClickException('no codeReviewer config found')

    def code_reviewer(self):
        """Lazily create and return code reviewer object."""
        if self._code_reviewer is None:
            self._code_reviewer = code_reviewer_factory.from_config(self.code_reviewer_config())
        return self._code_reviewer

    def scm_host_config(self):
        """Return scmHost config or raise ClickException if it is missing."""
        try:
            return self.user_config()['scmHost']
        except KeyError:
            raise click.ClickException('no scmHost config found in ~/zazuconfig.yaml')

    def scm_hosts(self):
        """Lazily create and return scm host list."""
        if self._scm_hosts is None:
            self._scm_hosts, self._default_scm_host = scm_host_factory(self.user_config(), self.scm_host_config())
        return self._scm_hosts

    def default_scm_host(self):
        """Lazily create scm host list and return the default scm host."""
        self.scm_hosts()
        return self._default_scm_host

    def scm_host_repo(self, repository):
        """Find a scm_host repo with a given name."""
        default_prefixed_id = '/'.join([self.default_scm_host(), repository])

        def match_host(host, id):
            full_id = '/'.join([host, id])
            return full_id == repository or full_id == default_prefixed_id

        for host_name, host in self.scm_hosts().iteritems():
            try:
                scm_repo = next((r for r in host.repos() if match_host(host_name, r.id)), None)
            except IOError:
                zazu.util.warn('unable to connect to "{}" SCM host'.format(host_name))
                scm_repo = None
            if scm_repo is not None:
                return scm_repo

    def project_config(self):
        """Parse and return the zazu yaml configuration file."""
        if self._project_config is None:
            self.check_repo()
            self._project_config = find_and_load_yaml_file([self.repo_root], PROJECT_FILE_NAMES)
            required_zazu_version = self._project_config.get('zazu', '')
            if required_zazu_version and required_zazu_version != zazu.__version__:
                zazu.util.warn('this repo has requested zazu {}, which doesn\'t match the installed version ({}). '
                               'Use "zazu upgrade" to fix this'.format(required_zazu_version, zazu.__version__))
        return self._project_config

    def user_config(self):
        """Parse and return the global zazu yaml configuration file."""
        if self._user_config is None:
            self._user_config = ConfigFile(user_config_filepath()).dict
        return self._user_config

    def stylers(self):
        """Lazily create Styler objects from the style config."""
        if self._stylers is None:
            self._stylers = styler_factory(self.project_config().get('style', {}))
        return self._stylers

    def develop_branch_name(self):
        """Get the branch name for develop branch."""
        try:
            return self.project_config()['branches']['develop']
        except (click.ClickException, KeyError):
            pass
        return 'develop'

    def master_branch_name(self):
        """Get the branch name for master branch."""
        try:
            return self.project_config()['branches']['master']
        except (click.ClickException, KeyError):
            pass
        return 'master'

    def protected_branches(self):
        """Return set of protected branches that can't be deleted."""
        return {self.develop_branch_name(), self.master_branch_name()}

    def zazu_version_required(self):
        """Return the version of zazu requested by the config file."""
        return self.project_config().get('zazu', '')

    def check_repo(self):
        """Check that the config has a valid repo set."""
        if self.repo_root is None or self.repo is None:
            raise click.UsageError('The current working directory is not in a git repo')


pass_config = click.make_pass_decorator(Config, ensure=True)


def maybe_write_default_user_config(path):
    """Write a default user config file if it doesn't exist."""
    DEFAULT_USER_CONFIG = """# User configuration file for zazu.
    
# SCM hosts are cloud hosting services for repos. Currently GitHub is supported.
# scmHost:
#    default:                # This is the default SCM host.
#        type: github        # Type of this SCM host.
#        user: user          # GitHub username
"""
    if not os.path.isfile(path):
        with open(path, 'w') as f:
            f.write(DEFAULT_USER_CONFIG)


def complete_param(ctx, args, incomplete):
    """Completion function that returns parameter names."""
    if '--add' in args:
        return []  # Don't offer completions when adding new params.
    config_file = ConfigFile(user_config_filepath())
    config_dict = config_file.dict
    flattened = zazu.util.flatten_dict(config_dict)
    return sorted([param for param in flattened.keys() if incomplete in param])


@click.command()
@click.pass_context
@click.option('-l', '--list', is_flag=True, help='list config')
@click.option('--show-origin', is_flag=True, help='show origin of each config variable, (implies --list)')
@click.option('--add', is_flag=True, help='add a new variable')
@click.option('--unset', is_flag=True, help='remove a variable')
@click.argument('param_name', required=False, type=str, autocompletion=complete_param)
@click.argument('param_value', required=False, type=str)
def config(ctx, list, add, unset, show_origin, param_name, param_value):
    """Manage zazu user configuration."""
    if not any([list, add, show_origin, param_name, param_value]):
        print(ctx.get_help())
        ctx.exit(-1)
    if (add + unset + list) > 1:
        raise click.UsageError('--add, --unset, --list, --edit are mutually exclusive')
    if (add or unset) and param_name is None:
        raise click.UsageError('--add and --unset requires a param name')
    if add and param_value is None:
        raise click.UsageError('--add requires a param value')
    if (list or show_origin) and param_name is not None:
        raise click.UsageError('--list and --show-origin can\'t be used with a param name')

    user_config_path = user_config_filepath()
    maybe_write_default_user_config(user_config_path)

    config_file = ConfigFile(user_config_path)
    config_dict = config_file.dict

    write_config = False

    if list or show_origin:
        source = '{}\t'.format(user_config_path) if show_origin else ''
        flattened = zazu.util.flatten_dict(config_dict)
        for k in sorted(flattened):
            click.echo('{}{}={}'.format(source, k, flattened[k]))

    elif param_name is not None:
        param_name_keys = param_name.split('.')
        if param_value is None:
            param_value = zazu.util.dict_get_nested(config_dict, param_name_keys, None)
            if param_value is None:
                raise click.ClickException('Param {} is unknown'.format(param_name))
            if unset:
                zazu.util.dict_del_nested(config_dict, param_name_keys)
                write_config = True
            else:
                click.echo(param_value)
                return
        else:
            # Write the new parameter value.
            if not add and zazu.util.dict_get_nested(config_dict, param_name_keys, None) is None:
                raise click.ClickException('Param {} is unknown, use --add to add it'.format(param_name))
            new_param_dict = zazu.util.unflatten_dict({param_name: param_value})
            zazu.util.dict_update_nested(config_dict, new_param_dict)
            write_config = True

    if write_config:
        # Update config file.
        config_file.write()
