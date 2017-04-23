# -*- coding: utf-8 -*-
"""Defines helper functions for tool install/uninstall"""
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'io',
    'os',
    'platform',
    'requests',
    'shutil',
    'tarfile'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"

package_path = os.path.expanduser(os.path.join('~', '.zazu', 'tools'))


class ToolInstallFunctions:
    """Holds a checker fn, installer fn, and uninstaller fn"""

    def __init__(self, check, install, uninstall):
        self.check_fn = check
        self.install_fn = install
        self.uninstall_fn = uninstall


class ToolEnforcer:
    """Holds a name, version and functions"""

    def __init__(self, name, version, functions):
        self.name = name
        self.version = version
        self.functions = functions

    def check(self):
        return self.functions.check_fn(self.name, self.version)

    def install(self):
        return self.functions.install_fn(self.name, self.version)

    def uninstall(self):
        return self.functions.uninstall_fn(self.name, self.version)


def get_install_path(name, version):
    return os.path.join(package_path, name, version)


def make_install_path(name, version):
    """Creates installation directory"""
    path = get_install_path(name, version)
    ensure_directory_exists(path)
    return path


def ensure_directory_exists(path):
    """Ensures that a directory exists"""
    try:
        os.makedirs(path)
    except OSError:
        pass


def check_token_file_exists(name, version):
    """check if the token file exists"""
    return os.path.exists(token_file(name, version))


def token_file(name, version):
    """Returns the path to the token file"""
    return os.path.join(get_install_path(name, version), 'ZAZU_INSTALLED')


def touch_token_file(name, version):
    """Creates a token file in the installation folder"""
    with open(token_file(name, version), 'a'):
        pass


def download_with_progress_bar(name, url):
    """Download a URL with a progress bar"""
    ret = b''
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        total_size = int(r.headers.get('content-length'))
        with click.progressbar(length=total_size, label='Downloading {}'.format(name)) as bar:
            for chunk in r.iter_content(chunk_size=1024):
                ret += chunk
                bar.update(len(chunk))
    return ret


def download_extract_tar_to_folder(name, url, path):
    """Download and extracts a (optionally zipped) tarfile and extracts it to a folder"""
    r = download_with_progress_bar(name, url)
    ensure_directory_exists(path)
    shutil.rmtree(path)
    ensure_directory_exists(path)
    click.echo('Extracting to "{}"...'.format(path))
    file_like_object = io.BytesIO(r)
    with tarfile.open(fileobj=file_like_object) as f:
        f.extractall(path)


def install_tar_file_from_url(name, version, url_map):
    """Download and install a (optionally zipped) tar file from a URL and
    extracts it to the proper installation folder"""
    try:
        url = url_map[platform.system()][platform.machine()]
        path = make_install_path(name, version)
        download_extract_tar_to_folder(name, url, path)
        touch_token_file(name, version)
        return True
    except KeyError:
        raise click.ClickException('Unsupported platform {} or arch {}'.format(platform.system(), platform.machine()))


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
    return install_tar_file_from_url(name, version, toolchains)


def install_gcc_arm_none_eabi_4_9_2015_q1(name, version):
    """Installs gcc-arm-none-eabi-4.9 2015-q1"""
    toolchains = {
        'Linux': {
            'x86_64': 'https://launchpad.net/gcc-arm-embedded/4.9/4.9-2015-q1-update/+download/gcc-arm-none-eabi-4_9-2015q1-20150306-linux.tar.bz2'
        },
        'Darwin': {
            'x86_64': 'https://launchpad.net/gcc-arm-embedded/4.9/4.9-2015-q1-update/+download/gcc-arm-none-eabi-4_9-2015q1-20150306-mac.tar.bz2'
        }
    }
    return install_tar_file_from_url(name, version, toolchains)


def install_gcc_arm_none_eabi_4_7_2014_q2(name, version):
    """Installs gcc-arm-none-eabi-4.7 2014-q2"""
    toolchains = {
        'Linux': {
            'x86_64': 'https://launchpad.net/gcc-arm-embedded/4.7/4.7-2014-q2-update/+download/gcc-arm-none-eabi-4_7-2014q2-20140408-linux.tar.bz2'
        },
        'Darwin': {
            'x86_64': 'https://launchpad.net/gcc-arm-embedded/4.7/4.7-2014-q2-update/+download/gcc-arm-none-eabi-4_7-2014q2-20140408-mac.tar.bz2'
        }
    }
    return install_tar_file_from_url(name, version, toolchains)


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
                '4.9': ToolInstallFunctions(check_token_file_exists, install_linaro_4_9_2014_05, uninstall_folder)
            },
        'gcc-arm-none-eabi':
            {
                '4.7': ToolInstallFunctions(check_token_file_exists, install_gcc_arm_none_eabi_4_7_2014_q2, uninstall_folder),
                '4.9': ToolInstallFunctions(check_token_file_exists, install_gcc_arm_none_eabi_4_9_2015_q1, uninstall_folder)
            }
    }
    return tools


def get_enforcer(name, version):
    """Gets a specific tool enforcer"""
    reg = get_tool_registry()
    try:
        versions = reg[name]
        try:
            enforcer = ToolEnforcer(name, version, versions[version])
        except KeyError:
            known_versions = zazu.util.pprint_list(sorted(versions.keys()))
            raise click.ClickException("Version {} not found for tool {}, choose from:{}".format(version,
                                                                                                 name,
                                                                                                 known_versions))
    except KeyError:
        raise click.ClickException('Tool {} not found'.format(name))

    return enforcer


def parse_install_spec(spec):
    """Splits version spec into name and version number"""
    components = spec.split('==')
    name = components[0]
    version = None
    if len(components) == 2:
        version = components[1]
    return name, version


def install_spec(spec, force=False, echo=lambda x: x):
    """Installs a known spec"""
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
    """Uninstalls a known spec"""
    name, version = parse_install_spec(spec)
    enforcer = get_enforcer(name, version)
    if enforcer.check():
        echo('Uninstalling {}...'.format(spec))
        enforcer.uninstall()
    else:
        echo('{} is not installed'.format(spec))
