# -*- coding: utf-8 -*-
"""config classes and methods for zazu"""
import os
import click
import git
import straight.plugin
import yaml
import zazu.build_server
import zazu.issue_tracker


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
                                                                                                    known_types.keys()))
    else:
        raise zazu.ZazuException('IssueTracker config requires a "type" field')


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
            raise zazu.ZazuException('{} is not a known CI service, please choose from {}'.format(type,
                                                                                                  known_types.keys()))
    else:
        raise zazu.ZazuException('CI config requires a "type" field')


def path_gen(search_paths, file_names):
    """Generates full paths given a list of directories and list of file names"""
    for p in search_paths:
        for f in file_names:
            yield os.path.join(p, f)


def load_yaml_file(search_paths, file_names):
    """Load a project yaml file"""
    searched = path_gen(search_paths, file_names)
    for file in searched:
        try:
            with open(file) as f:
                return yaml.load(f)
        except IOError:
            pass
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
        self._continuous_integration = None
        self._project_config = None
        self._tc = None

    def issue_tracker(self):
        if self._issue_tracker is None:
            try:
                self._issue_tracker = issue_tracker_factory(self.issue_tracker_config())
            except zazu.ZazuException as e:
                raise click.ClickException(str(e))
        return self._issue_tracker

    def issue_tracker_config(self):
        try:
            return self.project_config()['issueTracker']
        except KeyError:
            raise zazu.ZazuException("no issueTracker config found")

    def continuous_integration(self):
        if self._continuous_integration is None:
            try:
                self._continuous_integration = continuous_integration_factory(self.ci_config())
            except zazu.ZazuException as e:
                raise click.ClickException(str(e))
        return self._continuous_integration

    def ci_config(self):
        return self.project_config().get('ci', {})

    def project_config(self):
        if self._project_config is None:
            self._project_config = load_yaml_file([self.repo_root], PROJECT_FILE_NAMES)
            required_zazu_version = self.zazu_version_required()
            if required_zazu_version and required_zazu_version != zazu.__version__:
                click.secho('Warning: this repo has requested zazu {}, which doesn\'t match the installed version ({}). '
                            'Use "zazu upgrade" to fix this'.format(required_zazu_version, zazu.__version__), fg='red')
        return self._project_config

    def style_config(self):
        return self.project_config().get('style', {})

    def zazu_version_required(self):
        return self.project_config().get('zazu', '')

    def check_repo(self):
        """Checks that the config has a valid repo set"""
        if self.repo_root is None or self.repo is None:
            raise click.UsageError('The current working directory is not in a git repo')
