# -*- coding: utf-8 -*-
"""Config classes and methods for zazu."""
import zazu.build_server
import zazu.code_reviewer
import zazu.issue_tracker
import zazu.scm_host
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'git',
    'os',
    'ruamel.yaml',
    'straight.plugin',
    'subprocess',
    'sys'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"

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
            type = config['type'].lower()
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
build_server_factory = PluginFactory('buildServer', zazu.build_server.BuildServer)


def scm_host_factory(config):
    """Make and initialize the ScmHosts from the config."""
    hosts = {}
    plugins = straight.plugin.load('zazu.plugins', subclasses=zazu.scm_host.ScmHost)
    known_types = {p.type(): p for p in plugins}
    for name, config in config.iteritems():
        if 'type' in config:
            type = config['type'].lower()
            if type in known_types:
                hosts[name] = known_types[type].from_config(config)
            else:
                raise click.ClickException('{} is not a known ScmHost, please choose from {}'.format(type,
                                                                                                     sorted(known_types.keys())))
        else:
            raise click.ClickException('scmHost config requires a "type" field')

    return hosts


def styler_factory(config):
    """Make and initialize the Stylers from the config."""
    stylers = []
    plugins = straight.plugin.load('zazu.plugins', subclasses=zazu.styler.Styler)
    known_types = {p.type(): p for p in plugins}
    excludes = config.get('exclude', [])
    for k in config.keys():
        if k not in ['exclude', 'include']:
            if k in known_types:
                includes = config.get('include', known_types[k].default_extensions())
                stylers.append(known_types[k].from_config(config[k], excludes, includes))
            else:
                raise click.ClickException('{} is not a known styler, please choose from {}'.format(k,
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
        except ruamel.yaml.YAMLError as e:
            error_string = ''
            if hasattr(e, 'problem_mark'):
                error_line = get_line(filepath, e.problem_mark.line)
                col_indicator = make_col_indicator(e.problem_mark.column)
                error_string = "invalid_syntax: '{}'\n" \
                               "                 {}".format(error_line, col_indicator)
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
    return os.path.join(os.path.expanduser("~"), '.zazuconfig')


class Config(object):
    """Hold all zazu configuration info."""

    def __init__(self, repo_root):
        """Constructor, doesn't parse configuration or require repo to be valid."""
        self.repo_root = repo_root
        if self.repo_root is not None:
            try:
                self.repo = git.Repo(self.repo_root)
            except git.InvalidGitRepositoryError:
                self.repo = None
        self._issue_tracker = None
        self._code_reviewer = None
        self._scm_hosts = None
        self._build_server = None
        self._project_config = None
        self._user_config = None
        self._stylers = None
        self._tc = None

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
            raise click.ClickException("no issueTracker config found")

    def build_server(self):
        """Lazily create a build server object."""
        if self._build_server is None:
            self._build_server = build_server_factory.from_config(self.ci_config())
        return self._build_server

    def ci_config(self):
        """Return the CI configuration if one exists."""
        return self.project_config().get('ci', {})

    def code_reviewer_config(self):
        """Return the code reviewer configuration if one exists.

        Raises:
           click.ClickException: if no code review configuration is present.

        """
        try:
            return self.project_config()['codeReviewer']
        except KeyError:
            raise click.ClickException("no codeReviewer config found")

    def code_reviewer(self):
        """Lazily create and return code reviewr object."""
        if self._code_reviewer is None:
            self._code_reviewer = code_reviewer_factory.from_config(self.code_reviewer_config())
        return self._code_reviewer

    def scm_host_config(self):
        try:
            return self.user_config()['scmHost']
        except KeyError:
            raise click.ClickException("no scm config found")

    def scm_hosts(self):
        """Lazily create and return scm host list."""
        if self._scm_hosts is None:
            self._scm_hosts = scm_host_factory(self.scm_host_config())
        return self._scm_hosts

    def project_config(self):
        """Parse and return the zazu yaml configuration file."""
        if self._project_config is None:
            self.check_repo()
            self._project_config = find_and_load_yaml_file([self.repo_root], PROJECT_FILE_NAMES)
            required_zazu_version = self._project_config.get('zazu', '')
            if required_zazu_version and required_zazu_version != zazu.__version__:
                click.secho('Warning: this repo has requested zazu {}, which doesn\'t match the installed version ({}). '
                            'Use "zazu upgrade" to fix this'.format(required_zazu_version, zazu.__version__), fg='red')
        return self._project_config

    def user_config(self):
        """Parse and return the global zazu yaml configuration file."""
        if self._user_config is None:
            self._user_config = load_yaml_file(user_config_filepath())
        return self._user_config

    def stylers(self):
        """Lazily create Styler objects from the style config."""
        if self._stylers is None:
            self._stylers = styler_factory(self.project_config().get('style', {}))
        return self._stylers

    def zazu_version_required(self):
        """Return the version of zazu requested by the config file."""
        return self.project_config().get('zazu', '')

    def check_repo(self):
        """Check that the config has a valid repo set."""
        if self.repo_root is None or self.repo is None:
            raise click.UsageError('The current working directory is not in a git repo')


DEFAULT_USER_CONFIG = """# Default user configuration for zazu

# scm:
#  github:
#    type: github
#    user: username

"""


@click.command()
@click.pass_context
@click.option('-l', '--list', is_flag=True, help='list config')
@click.option('--show-origin', is_flag=True, help='show origin of each config variable, (implies --list)')
@click.option('-e', '--edit', is_flag=True, help='open config file in an editor')
@click.option('--add', is_flag=True, help='add a new variable')
@click.option('--unset', is_flag=True, help='remove a variable')
@click.argument('param_name', required=False)
@click.argument('param_value', required=False)
def config(ctx, list, edit, add, unset, show_origin, param_name, param_value):
    """Manage zazu user configuration."""
    if not any([list, edit, add, show_origin, param_name, param_value]):
        print(ctx.get_help())
        ctx.exit(-1)
    if (add + unset + list + edit) > 1:
        raise click.UsageError('--add, --unset, --list, --edit are mutually exclusive')
    if (add or unset) and param_name is None:
        raise click.UsageError('--add and --unset requires a param name')
    if add and param_value is None:
        raise click.UsageError('--add requires a param value')
    if (list or show_origin) and param_name is not None:
        raise click.UsageError('--list and --show_origin can\'t be used with a param name')

    user_config_path = user_config_filepath()
    if not os.path.isfile(user_config_path):
        with open(user_config_path, 'w') as f:
            f.write(DEFAULT_USER_CONFIG)

    config_dict = load_yaml_file(user_config_path)
    flattened = zazu.util.flatten_dict(config_dict)
    write_config = False

    if list or show_origin:
        source = '{}\t'.format(user_config_path) if show_origin else ''
        for k, v in flattened.items():
            print('{}{}={}'.format(source, k, v))

    elif edit:
        while True:
            params = ['{}={}'.format(k, v) for k, v in flattened.iteritems()]
            picked = zazu.util.pick(params + ['Done'], 'Choose a parameter to edit')
            param_name = picked.split('=', 1)[0]
            if param_name is 'Done':
                break
            param_value = zazu.util.prompt('New value for {}'.format(param_name))
            flattened[param_name] = str(param_value)
            write_config = True

    elif param_name is not None:
        if param_value is None:
            param_value = flattened.get(param_name, None)
            if param_value is None:
                ctx.exit(-1)
            if unset:
                del flattened[param_name]
            else:
                print(param_value)
                return
        else:
            # Write the new parameter value.
            if not add and flattened.get(param_name, None) is None:
                raise click.ClickException('Param {} is unknown, use --add to add it'.format(param_name))
            flattened[param_name] = str(param_value)
            write_config = True

    if write_config:
        # Update config file.
        config_dict.update(zazu.util.unflatten_dict(flattened))
        yaml = ruamel.yaml.YAML()
        with open(user_config_path, 'w') as f:
            yaml.dump(config_dict, f)
