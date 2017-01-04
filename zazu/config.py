# -*- coding: utf-8 -*-
"""config classes and methods for zazu"""
import os
import click
import git
import jira
import teamcity_helper
import yaml
import zazu.credential_helper


class IssueTracker(object):
    pass


class IssueTrackerError(Exception):
    """Parent of all IssueTracker errors"""


class ZazuException(Exception):
    """Parent of all Zazu errors"""

    def __init___(self, error):
        Exception.__init__("Error: {}".format(error))


PROJECT_FILE_NAMES = ['zazu.yaml', '.zazu.yaml']
ZAZU_IMAGE_URL = 'http://vignette1.wikia.nocookie.net/disney/images/c/ca/Zazu01cf.png'
ZAZU_REPO_URL = 'https://github.com/LilyRobotics/zazu'
JIRA_CREATED_BY_ZAZU = '----\n!{}|width=20! Created by [Zazu|{}]'.format(ZAZU_IMAGE_URL, ZAZU_REPO_URL)


class JiraIssueTracker(IssueTracker):
    """Implements zazu issue tracker interface for JIRA"""

    def __init__(self, base_url, default_project, components):
        self._base_url = base_url
        self._default_project = default_project
        self._components = components
        self._jira_handle = None

    def connect(self):
        """Get handle to ensure that JIRA credentials are in place"""
        self.jira_handle()

    @staticmethod
    def closed(issue):
        return str(issue.fields.status) == 'Closed'

    @staticmethod
    def resolved(issue):
        return str(issue.fields.status) == 'Resolved'

    def jira_handle(self):
        if self._jira_handle is None:
            username, password = zazu.credential_helper.get_user_pass_credentials('Jira')
            self._jira_handle = jira.JIRA(self._base_url,
                                          basic_auth=(username, password),
                                          options={'check_update': False}, max_retries=0)
        return self._jira_handle

    def browse_url(self, issue_id):
        return '{}/browse/{}'.format(self._base_url, issue_id)

    def issue(self, issue_id):
        try:
            ret = self.jira_handle().issue(issue_id)
        except jira.exceptions.JIRAError as e:
            raise IssueTrackerError(str(e))
        return ret

    def create_issue(self, project, issue_type, summary, description, component):
        try:
            issue_dict = {
                'project': {'key': project},
                'issuetype': {'name': issue_type},
                'summary': summary,
                'description': '{}\n\n{}'.format(description, JIRA_CREATED_BY_ZAZU)
            }
            if component is not None:
                issue_dict['components'] = [{'name': component}]
            return self.jira_handle().create_issue(issue_dict)
        except jira.exceptions.JIRAError as e:
            raise IssueTrackerError(str(e))

    def assign_issue(self, issue, assignee):
        try:
            self.jira_handle().assign_issue(issue, assignee)
        except jira.exceptions.JIRAError as e:
            raise IssueTrackerError(str(e))

    def default_project(self):
        return self._default_project

    def issue_types(self):
        return ['Task', 'Bug', 'Story']

    def issue_components(self):
        return self._components

    @staticmethod
    def from_config(config):
        """Makes a IssueTrackerJira from a config"""
        try:
            url = config['url']
        except KeyError:
            raise ZazuException('Jira config requires a "url" field')
        try:
            project = config['project']
        except KeyError:
            raise ZazuException('Jira config requires a "project" field')
        components = config.get('component', None)
        if not isinstance(components, list):
            components = [components]
        return JiraIssueTracker(url, project, components)


def issue_tracker_factory(config):
    """A factory function that makes and initializes a IssueTracker object from a config"""
    known_types = {'jira': JiraIssueTracker.from_config}
    if 'type' in config:
        type = config['type']
        type = type.lower()
        if type in known_types:
            return known_types[type](config)
        else:
            raise ZazuException('{} is not a known issueTracker, please choose from {}'.format(type,
                                                                                               known_types.keys()))
    else:
        raise ZazuException('IssueTracker config requires a "type" field')


def continuous_integration_factory(config):
    """A factory function that makes and initializes a CI object from a config"""
    known_types = {'teamcity': teamcity_helper.TeamCityHelper.from_config}
    if 'type' in config:
        type = config['type']
        type = type.lower()
        if type in known_types:
            return known_types[type](config)
        else:
            raise ZazuException('{} is not a known CI service, please choose from {}'.format(type,
                                                                                             known_types.keys()))
    else:
        raise ZazuException('CI config requires a "type" field')


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
            except ZazuException as e:
                raise click.ClickException(str(e))
        return self._issue_tracker

    def issue_tracker_config(self):
        try:
            return self.project_config()['issueTracker']
        except KeyError:
            raise ZazuException("no issueTracker config found")

    def continuous_integration(self):
        if self._continuous_integration is None:
            try:
                self._continuous_integration = continuous_integration_factory(self.ci_config())
            except ZazuException as e:
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
