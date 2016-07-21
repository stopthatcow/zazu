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
    install_requires=['click==6.6',
                      'requests==2.10.0',
                      'PyGithub==1.26.0',
                      'jira==1.0.7.dev20160607111203',
                      'GitPython==2.0.7',
                      'pyteamcity==0.0.1',
                      'pyyaml==3.11',
                      'keyring==9.3.1',
                      'autopep8==1.2.4',
                      'semantic_version==2.5.0',
                      'gcovr==3.2',
                      'teamcity-messages==1.19',
                      'futures==3.0.5'],
    entry_points='''
        [console_scripts]
        zazu=zazu.core:cli
        '''
)

