# -*- coding: utf-8 -*-
"""Config classes and methods for zazu."""
import zazu.build_server
import zazu.code_reviewer
import zazu.issue_tracker
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'git',
    'os',
    'straight.plugin',
    'yaml'
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
            type = config['type']
            type = type.lower()
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


def styler_factory(config):
    """Make and initialize the Stylers from the config."""
    stylers = []
    plugins = straight.plugin.load('zazu.plugins', subclasses=zazu.styler.Styler)
    known_types = {p.type(): p for p in plugins}
    excludes = config.get('exclude', [])
    for k, v in config.iteritems():
        if k not in ['exclude', 'include']:
            if k in known_types:
                v = {} if v is None else v
                includes = config.get('include', known_types[k].default_extensions())
                stylers.append(known_types[k].from_config(v, excludes, includes))
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


def load_yaml_file(search_paths, file_names):
    """Load a project yaml file."""
    searched = path_gen(search_paths, file_names)
    for file_name in searched:
        try:
            with open(file_name, 'r') as f:
                try:
                    config = yaml.load(f)
                except yaml.YAMLError as e:
                    if hasattr(e, 'problem_mark'):
                        error_line = get_line(file_name, e.problem_mark.line)
                        col_indicator = make_col_indicator(e.problem_mark.column)
                        error_string = "invalid_syntax: '{}'\n" \
                                       "                 {}".format(error_line, col_indicator)
                    raise click.ClickException('unable to parse config file \'{}\'\n{}'.format(file_name, error_string))
                return config
        except IOError:
            pass
    # need a new generator
    searched = path_gen(search_paths, file_names)
    raise click.ClickException('no yaml file found, searched:{}'.format(zazu.util.pprint_list(searched)))


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
        self._build_server = None
        self._project_config = None
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

    def project_config(self):
        """Parse and return the zazu yaml configuration file."""
        if self._project_config is None:
            self.check_repo()
            self._project_config = load_yaml_file([self.repo_root], PROJECT_FILE_NAMES)
            required_zazu_version = self._project_config.get('zazu', '')
            if required_zazu_version and required_zazu_version != zazu.__version__:
                click.secho('Warning: this repo has requested zazu {}, which doesn\'t match the installed version ({}). '
                            'Use "zazu upgrade" to fix this'.format(required_zazu_version, zazu.__version__), fg='red')
        return self._project_config

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
