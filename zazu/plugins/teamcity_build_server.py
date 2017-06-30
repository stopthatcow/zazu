# -*- coding: utf-8 -*-
"""Defines helper functions for teamcity interaction"""
import zazu.build_server
import zazu.credential_helper
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'json',
    'pyteamcity',
    'requests',
    'teamcity.messages'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class TeamCityBuildServer(zazu.build_server.BuildServer, pyteamcity.TeamCity):
    """Extends the pyteamcity.Teamcity object to expose interfaces to create projects and build configurations"""

    def __init__(self, address, port=80, protocol='http'):
        self._address = address
        self._protocol = protocol
        self._port = port
        self._tc_handle = None

    def teamcity_handle(self):
        if self._tc_handle is None:
            use_saved_credentials = True
            while True:
                tc_user, tc_pass = zazu.credential_helper.get_user_pass_credentials('TeamCity', use_saved_credentials)
                tc = pyteamcity.TeamCity(username=tc_user, password=tc_pass,
                                         server=self._address, port=self._port,
                                         protocol=self._protocol)
                try:
                    tc.get_user_by_username(tc_user)
                    self._tc_handle = tc
                    break
                except pyteamcity.HTTPError:
                    click.echo("incorrect username or password!")
                    use_saved_credentials = False

        return self._tc_handle

    def setup_vcs_root(self, name, parent_project_id, git_url):
        vcs_root = {
            'name': str(name),
            'id': '{}_{}'.format(parent_project_id, name),
            'vcsName': 'jetbrains.git',
            'project': {'id': str(parent_project_id)},
            'properties': {
                'property': [
                    {'name': 'agentCleanFilesPolicy',
                     'value': 'ALL_UNTRACKED'},
                    {'name': 'agentCleanPolicy',
                     'value': 'ON_BRANCH_CHANGE'},
                    {"name": "authMethod",
                     "value": "TEAMCITY_SSH_KEY"},
                    {"name": "teamcitySshKey",
                     "value": "TeamCity SSH Key"},
                    {'name': 'branch',
                     'value': 'refs/heads/develop'},
                    {'name': 'ignoreKnownHosts',
                     'value': 'true'},
                    {'name': 'submoduleCheckout',
                     'value': 'CHECKOUT'},
                    {'name': 'teamcity:branchSpec',
                     'value': '+:refs/heads/develop\n+:refs/heads/master\n+:refs/pull/(*/merge)'},
                    {'name': 'url',
                     'value': str(git_url)},
                    {'name': 'useAlternates',
                     'value': 'true'},
                    {'name': 'username',
                     'value': 'git'},
                    {'name': 'usernameStyle',
                     'value': 'USERID'}
                ]
            }
        }
        try:
            ret = self.teamcity_handle().get_vcs_root_by_vcs_root_id(vcs_root['id'])
            for p in vcs_root['properties']['property']:
                self._put_helper('vcs-roots/{}/properties/{}'.format(vcs_root['id'], p['name']), str(p['value']),
                                 content_type='text/plain')
        except pyteamcity.HTTPError:
            ret = self._post_helper('vcs-roots', vcs_root)
        return ret

    def setup_project(self, name, description, parent_project_id):
        project_data = {
            'name': name,
            'description': description
        }
        if parent_project_id is not None:
            id = '{}_{}'.format(parent_project_id, name)
        else:
            id = name
        try:
            ret = self.teamcity_handle().get_project_by_project_id(id)
            # TODO update description
            for k, v in project_data.items():
                self._put_helper('projects/{}/{}'.format(id, k), str(v), content_type='text/plain')
            ret = self.teamcity_handle().get_project_by_project_id(id)
        except pyteamcity.HTTPError:
            if parent_project_id is not None:
                project_data['parentProject'] = {'id': parent_project_id}
            project_data['id'] = id
            ret = self._post_helper('projects', project_data)
        return ret

    def add_vcs_root_to_build(self, vcs_root_id, build_config_id):
        vcs_root_entry = {
            "id": str(vcs_root_id),
            "checkout-rules": "",
            "vcs-root": {
                "id": str(vcs_root_id)
            }
        }
        return self._post_helper('buildTypes/id:{}/vcs-root-entries'.format(build_config_id), vcs_root_entry)

    def add_template_to_build(self, template_id, build_config_id):
        return self._put_helper('buildTypes/id:{}/template'.format(build_config_id), template_id,
                                content_type='text/plain', accept_type='application/json')

    def add_parameters_to_build(self, parameters, build_config_id):
        for k, v in parameters.items():
            self._put_helper('buildTypes/id:{}/parameters/{}'.format(build_config_id, k), str(v),
                             content_type='text/plain')

    def apply_settings_to_build(self, settings, build_config_id):
        for k, v in settings.items():
            self._put_helper('buildTypes/id:{}/settings/{}'.format(build_config_id, k), str(v),
                             content_type='text/plain')

    def add_agent_requirements_to_build(self, agent_requirements, build_config_id):
        for a in agent_requirements:
            request = {
                "id": a['name'],
                "type": a['type'],
                "properties": {
                    "count": 2,
                    "property": [
                        {
                            "name": "property-name",
                            "value": a['name']
                        },
                        {
                            "name": "property-value",
                            "value": a['value']
                        }
                    ]
                }
            }
            try:
                self._put_helper('buildTypes/id:{}/agent-requirements/{}'.format(build_config_id, request['id']), request)
            except Exception:
                self._post_helper('buildTypes/id:{}/agent-requirements'.format(build_config_id), request)

    def setup_build_configuration(self, name, description, parent_project_id,
                                  vcs_root_id, template_id, parameters, settings, agent_requirements):
        build_conf = {
            'name': str(name),
            'project': {
                'id': str(parent_project_id)
            }
        }
        if description is not None:
            build_conf['description'] = str(description),

        try:
            project = self.teamcity_handle().get_project_by_project_id(parent_project_id)
            build_types = project['buildTypes']['buildType']
            ret = [x for x in build_types if x['name'] == name][0]
        except (pyteamcity.HTTPError, IndexError):
            ret = self._post_helper(
                str('projects/id:{}/buildTypes').format(parent_project_id), build_conf)
        self.add_vcs_root_to_build(vcs_root_id, ret['id'])
        self.add_template_to_build(template_id, ret['id'])
        self.add_parameters_to_build(parameters, ret['id'])
        self.apply_settings_to_build(settings, ret['id'])
        self.add_agent_requirements_to_build(agent_requirements, ret['id'])
        return ret

    def _post_helper(self, uri, json_data):
        click.echo("POST to {} {}".format(uri, json.dumps(json_data)))
        ret = requests.post(str(self.teamcity_handle().base_url + '/' + uri),
                            auth=(self.teamcity_handle().username, self.teamcity_handle().password),
                            headers={'Accept': 'application/json'},
                            json=json_data)
        if 300 < ret.status_code >= 200:
            raise Exception("Request returned error code {}, {}".format(
                ret.status_code, ret.text))
        return ret.json()

    def _put_helper(self, uri, data, content_type='application/json', accept_type=None):
        if 'application/json' in content_type:
            data = json.dumps(data)
        click.echo("PUT to {} {}".format(uri, data))
        if accept_type is None:
            accept_type = content_type
        ret = requests.put(str(self.teamcity_handle().base_url + '/' + uri),
                           auth=(self.teamcity_handle().username, self.teamcity_handle().password),
                           headers={'Accept': accept_type,
                                    'Content-type': content_type},
                           data=data)
        if 300 < ret.status_code >= 200:
            raise Exception("Request returned error code {}, {}".format(
                ret.status_code, ret.text))
        if content_type == 'application/json':
            ret = ret.json()
        return ret

    @staticmethod
    def publish_artifacts(artifact_paths):
        if teamcity.is_running_under_teamcity():
            messenger = teamcity.messages.TeamcityServiceMessages()
            for a in artifact_paths:
                messenger.publishArtifacts(a)

    @staticmethod
    def type():
        return 'TeamCity'

    @staticmethod
    def from_config(config):
        try:
            url = config['url']
        except KeyError:
            raise zazu.ZazuException('TeamCity config requires a "url" field')

        from future.moves.urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.netloc:
            components = parsed.netloc.split(':')
            address = components.pop(0)
            try:
                port = int(components.pop(0))
            except IndexError:
                port = 80
            protocol = parsed.scheme

        else:
            raise zazu.ZazuException('Unable to parse Teamcity URL "{}"'.format(url))

        tc = TeamCityBuildServer(address=address,
                                 port=port,
                                 protocol=protocol)
        return tc

    def setup_component(self, component, repo_name, git_url):
        project_name = component.name()
        project_description = component.description()
        parent_project_id = self.setup_project(project_name, project_description, None)['id']
        vcs_root_id = self.setup_vcs_root(project_name, parent_project_id, git_url)['id']
        for g in component.goals().values():
            subproject_id = self.setup_project(
                g.name(), g.description(), parent_project_id)['id']
            for a in g.builds().values():
                template_id = 'ZazuGitHubLilyRoboticsDefault'
                parameters = {
                    'architecture': a.build_arch(),
                    'goal': g.name(),
                    'gitHubRepoPath': repo_name,
                    'buildType': a.build_type()
                }

                settings = {
                    'checkoutMode': 'ON_AGENT'
                }

                agent_requirements = []
                if 'win-msvc' in a.build_arch():
                    agent_requirements.append({
                        'name': "teamcity.agent.jvm.os.name",
                        'type': 'contains',
                        'value': 'Windows'
                    })
                else:
                    agent_requirements.append({
                        'name': "teamcity.agent.jvm.os.name",
                        'type': 'equals',
                        'value': 'Linux'
                    })
                self.setup_build_configuration(a.build_arch(),
                                               a.build_description(),
                                               subproject_id,
                                               vcs_root_id,
                                               template_id,
                                               parameters,
                                               settings,
                                               agent_requirements)

# Some ideas for more TC interaction:
# check status of builds associated with this branch
# add support for tagging builds (releases)
