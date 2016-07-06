# -*- coding: utf-8 -*-
"""Defines helper functions for teamcity interaction"""
import click
import requests
import platform
import io
import requests
import tarfile
import sys
import os
import shutil


class ToolEnforcer:

    def __init__(self, check, install, uninstall):
        self.check_fn = check
        self.install_fn = install
        self.uninstall_fn = uninstall

    def check(self):
        return self.check_fn(self._name, self._version)

    def install(self):
        return self.install_fn(self._name, self._version)

    def uninstall(self):
        return self.uninstall_fn(self._name, self._version)


package_path = os.path.expanduser(os.path.join('~', '.zazu', 'tools'))


def get_install_path(name, version):
    return os.path.join(package_path, name, version)


def make_install_path(name, version):
    path = get_install_path(name, version)
    try:
        os.makedirs(path)
    except OSError:
        pass
    return path


def check_exists(name, version):
    return os.path.exists(get_install_path(name, version))


def download_with_progress_bar(name, url):
    ret = b''
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        total_size = int(r.headers.get('content-length'))
        with click.progressbar(length=total_size, label='Downloading {}'.format(name)) as bar:
            for chunk in r.iter_content(chunk_size=1024):
                ret += chunk
                bar.update(len(chunk))
    return ret


def install_linaro_4_9_2014_05(name, version):
    """Installs Linaro gcc 4.9 2014-05"""
    toolchains = {
        'Linux': {
            'x86_64': 'https://github.com/LilyRobotics/toolchains/blob/master/gcc-linaro-4.9-2014.05-arm-linux-gnueabihf-x86_32-linux-gnu.tar.gz?raw=true'
        },
        'Darwin': {
            'x86_64': 'https://github.com/LilyRobotics/toolchains/blob/master/gcc-linaro-4.9-2014.05-arm-linux-gnueabihf-x86_64-darwin.tar.gz?raw=true'
        }
    }
    try:
        url = toolchains[platform.system()][platform.machine()]
        r = download_with_progress_bar(name, url)

        path = make_install_path(name, version)
        shutil.rmtree(path)
        make_install_path(name, version)
        click.echo('Extracting to "{}"...'.format(path))
        file_like_object = io.BytesIO(r)
        with tarfile.open(fileobj=file_like_object) as f:
            f.extractall(path)
            return True
    except KeyError:
        click.echo('Unsupported platform {} or arch {}'.format(platform.system(), platform.machine()))
        sys.exit(-1)


def uninstall_folder(name, version):
    """removes a installed directory and the parent if it is empty"""
    try:
        path = get_install_path(name, version)
        shutil.rmtree(path)
        parent_path = os.path.dirname(path)
        if not os.listdir(parent_path):
            shutil.rmtree(parent_path)
    except OSError:
        pass


def get_tool_registry():
    """Returns a dictionary of the known tools"""
    tools = {
        'gcc-linaro-arm-linux-gnueabihf':
            {
                '4.9': ToolEnforcer(check_exists, install_linaro_4_9_2014_05, uninstall_folder)
            }
    }
    return tools


def get_enforcer(name, version):
    """Gets a specific tool enforcer"""
    enforcer = None
    reg = get_tool_registry()
    try:
        versions = reg[name]
        try:
            enforcer = versions[version]
            enforcer._version = version
            enforcer._name = name
        except KeyError:
            click.echo("Version {} not found for tool {}, choose from:".format(version, name))
            for v in sorted(versions.keys()):
                click.echo('- {}'.format(v))
            sys.exit(-1)
    except KeyError:
        click.echo('Tool {} not found'.format(name))
        sys.exit(-1)

    return enforcer


def parse_install_spec(spec):
    components = spec.split('==')
    name = components[0]
    version = None
    if len(components) == 2:
        version = components[1]
    return name, version


def install_spec(spec, force=False, echo=lambda x: x):
    ret = 0
    name, version = parse_install_spec(spec)
    enforcer = get_enforcer(name, version)
    if force and enforcer.check():
        enforcer.uninstall()
    if not enforcer.check():
        echo('Installing {}...'.format(spec))
        ret = enforcer.install()
        if ret:
            echo('{} installed successfully'.format(spec))
        else:
            echo('Error while installing {}'.format(spec))
    else:
        echo('{} is already installed'.format(spec))
    return ret


def uninstall_spec(spec, echo=lambda x: x):
    name, version = parse_install_spec(spec)
    enforcer = get_enforcer(name, version)
    if enforcer.check():
        echo('Uninstalling {}...'.format(spec))
        enforcer.uninstall()
    else:
        echo('{} is not installed'.format(spec))
