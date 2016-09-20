# -*- coding: utf-8 -*-
"""config classes and methods for zazu"""
import click
import zazu.credential_helper
import git
import os
import yaml
import jira


class IssueTracker(object):
    pass


class IssueTrackerError(Exception):
    """Parent of all IssueTracker errors"""


class ZazuException(Exception):
    """Parent of all Zazu errors"""

    def __init___(self, error):
        Exception.__init__("Error: {}".format(error))


PROJECT_FILE_NAME = 'zazu.yaml'
ZAZU_IMAGE_URL = 'http://vignette1.wikia.nocookie.net/disney/images/c/ca/Zazu01cf.png'
ZAZU_REPO_URL = 'https://github.com/LilyRobotics/zazu'
JIRA_CREATED_BY_ZAZU = '----\n!{}|width=20! Created by [Zazu|{}]'.format(ZAZU_IMAGE_URL, ZAZU_REPO_URL)


class JiraIssueTracker(IssueTracker):
    """Implements zazu issue tracker interface for JIRA"""

    def __init__(self, base_url, default_project, default_component):
        self._base_url = base_url
        self._default_project = default_project
        self._default_component = default_component
        username, password = zazu.credential_helper.get_user_pass_credentials('Jira')
        self._jira_handle = jira.JIRA(self._base_url,
                                      basic_auth=(username, password),
                                      options={'check_update': False}, max_retries=0)

    def browse_url(self, issue_id):
        return '{}/browse/{}'.format(self._base_url, issue_id)

    def issue(self, issue_id):
        try:
            ret = self._jira_handle.issue(issue_id)
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
            return self._jira_handle.create_issue(issue_dict)
        except jira.exceptions.JIRAError as e:
            raise IssueTrackerError(str(e))

    def assign_issue(self, issue, assignee):
        try:
            self._jira_handle.assign_issue(issue, assignee)
        except jira.exceptions.JIRAError as e:
            raise IssueTrackerError(str(e))

    def default_project(self):
        return self._default_project

    def issue_types(self):
        return ['Task', 'Bug', 'Story']

    def default_component(self):
        return self._default_component

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
        component = config.get('component', None)
        return JiraIssueTracker(url, project, component)


def issue_tracker_factory(config):
    """A factory function that makes and initializes a IssueTracker object from a config"""
    known_issue_trackers = {'jira': JiraIssueTracker.from_config}
    if 'type' in config:
        type = config['type']
        type = type.lower()
        if type in known_issue_trackers:
            return known_issue_trackers[type](config)
        else:
            raise ZazuException('{} is not a known issueTracker, please choose from {}'.format(type,
                                                                                               known_issue_trackers.keys()))
    else:
        raise ZazuException('IssueTracker config requires a "type" field')


def load_project_file(path):
    """Load a project yaml file"""
    try:
        with open(path) as f:
            return yaml.load(f)
    except IOError:
        raise click.ClickException('no {} file found in this repo'.format(PROJECT_FILE_NAME))


class Config(object):

    """Holds all zazu configuration info"""

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.repo = git.Repo(self.repo_root)
        self._issue_tracker = None
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

    def ci_config(self):
        return self.project_config().get('ci', {})

    def project_config(self):
        if self._project_config is None:
            self._project_config = load_project_file(os.path.join(self.repo_root, PROJECT_FILE_NAME))
        return self._project_config

    def pep8_config(self):
        return {}

    def astyle_config(self):
        return {}

    def project_config(self):
        return load_project_file(os.path.join(self.repo_root, PROJECT_FILE_NAME))

    def check_repo(self):
        """Checks that the config has a valid repo set"""
        if self.repo_root is None or self.repo is None:
            raise click.UsageError('The current working directory is not in a git repo')
