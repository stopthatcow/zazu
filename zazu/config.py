# -*- coding: utf-8 -*-
"""config classes and methods for zazu"""
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


def issue_tracker_factory(config):
    """A factory function that makes and initializes a IssueTracker object from a config"""
    plugins = straight.plugin.load('zazu.plugins', subclasses=zazu.issue_tracker.IssueTracker)
    known_types = {p.type().lower(): p.from_config for p in plugins}
    if 'type' in config:
        type = config['type']
        type = type.lower()
        if type in known_types:
            return known_types[type](config)
        else:
            raise zazu.ZazuException('{} is not a known issueTracker, please choose from {}'.format(type,
                                                                                                    sorted(known_types.keys())))
    else:
        raise zazu.ZazuException('IssueTracker config requires a "type" field')


def code_reviewer_factory(config):
    """A factory function that makes and initializes a CodeReviewer object from a config"""
    plugins = straight.plugin.load('zazu.plugins', subclasses=zazu.code_reviewer.CodeReviewer)
    known_types = {p.type().lower(): p.from_config for p in plugins}
    if 'type' in config:
        type = config['type']
        type = type.lower()
        if type in known_types:
            return known_types[type](config)
        else:
            raise zazu.ZazuException('{} is not a known CodeReviewer, please choose from {}'.format(type,
                                                                                                    sorted(known_types.keys())))
    else:
        raise zazu.ZazuException('CodeReviewer config requires a "type" field')


def continuous_integration_factory(config):
    """A factory function that makes and initializes a CI object from a config"""
    plugins = straight.plugin.load('zazu.plugins', subclasses=zazu.build_server.BuildServer)
    known_types = {p.type().lower(): p.from_config for p in plugins}
    if 'type' in config:
        type = config['type']
        type = type.lower()
        if type in known_types:
            return known_types[type](config)
        else:
            raise click.ClickException('{} is not a known CI service, please choose from {}'.format(type,
                                                                                                    sorted(known_types.keys())))
    else:
        raise click.ClickException('CI config requires a "type" field')


def styler_factory(config):
    """A factory function that makes and initializes the stylers from the config"""
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
    """Generates full paths given a list of directories and list of file names"""
    for p in search_paths:
        for f in file_names:
            yield os.path.join(p, f)


def load_yaml_file(search_paths, file_names):
    """Load a project yaml file"""
    searched = path_gen(search_paths, file_names)
    for file_name in searched:
        try:
            with open(file_name) as f:
                config = yaml.load(f)
                if config is None:
                    raise click.ClickException('unable to parse config file')
                return config
        except IOError:
            pass
    # need a new generator
    searched = path_gen(search_paths, file_names)
    raise click.ClickException('no yaml file found, searched:{}'.format(zazu.util.pprint_list(searched)))


class Config(object):

    """Holds all zazu configuration info"""

    def __init__(self, repo_root):
        self.repo_root = repo_root
        if self.repo_root:
            self.repo = git.Repo(self.repo_root)
        else:
            self.repo = None
        self._issue_tracker = None
        self._code_reviewer = None
        self._continuous_integration = None
        self._project_config = None
        self._tc = None

    def issue_tracker(self):
        if self._issue_tracker is None:
            self._issue_tracker = issue_tracker_factory(self.issue_tracker_config())
        return self._issue_tracker

    def issue_tracker_config(self):
        try:
            return self.project_config()['issueTracker']
        except KeyError:
            raise click.ClickException("no issueTracker config found")

    def continuous_integration(self):
        if self._continuous_integration is None:
            self._continuous_integration = continuous_integration_factory(self.ci_config())
        return self._continuous_integration

    def ci_config(self):
        return self.project_config().get('ci', {})

    def code_reviewer_config(self):
        try:
            return self.project_config()['codeReviewer']
        except KeyError:
            raise click.ClickException("no codeReviewer config found")

    def code_reviewer(self):
        if self._code_reviewer is None:
            self._code_reviewer = code_reviewer_factory(self.code_reviewer_config())
        return self._code_reviewer

    def project_config(self):
        if self._project_config is None:
            self._project_config = load_yaml_file([self.repo_root], PROJECT_FILE_NAMES)
            required_zazu_version = self._project_config.get('zazu', '')
            if required_zazu_version and required_zazu_version != zazu.__version__:
                click.secho('Warning: this repo has requested zazu {}, which doesn\'t match the installed version ({}). '
                            'Use "zazu upgrade" to fix this'.format(required_zazu_version, zazu.__version__), fg='red')
        return self._project_config

    def stylers(self):
        return styler_factory(self.project_config().get('style', {}))

    def zazu_version_required(self):
        return self.project_config().get('zazu', '')

    def check_repo(self):
        """Checks that the config has a valid repo set"""
        if self.repo_root is None or self.repo is None:
            raise click.UsageError('The current working directory is not in a git repo')
