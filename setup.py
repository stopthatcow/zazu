# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os.path
root_path = os.path.dirname(os.path.abspath(__file__))
version_file_path = os.path.join(root_path, 'zazu', 'version.txt')

try:
    import pypandoc
    description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    description = ''

with open(version_file_path, 'r') as version_file:
    version = version_file.read()

setup(
    name='zazu',
    version=version,
    description='At your service for development workflow management',
    long_description=description,
    author='Nicholas Wiles',
    author_email='nic@lily.camera',
    url='https://github.com/LilyRobotics/zazu',
    license='BSD',
    packages=find_packages(exclude=('tests', 'docs')),
    package_data={'zazu': ['cmake/*.cmake', 'githooks/*', 'pypi/pip.conf', 'version.txt']},
    install_requires=['Click', 'requests', 'PyGithub',
                      'jira', 'GitPython', 'pyteamcity',
                      'pyyaml', 'keyring', 'autopep8',
                      'semantic_version', 'gcovr',
                      'teamcity-messages', 'futures'],
    entry_points='''
        [console_scripts]
        zazu=zazu.core:cli
        '''
)

