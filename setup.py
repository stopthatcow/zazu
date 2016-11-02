# -*- coding: utf-8 -*-

import setuptools
import os.path
root_path = os.path.dirname(os.path.abspath(__file__))
version_file_path = os.path.join(root_path, 'zazu', 'version.txt')

try:
    import pypandoc
    description = pypandoc.convert('README.md', 'rst')
except (OSError, IOError, ImportError):
    description = ''

try:
    with open(version_file_path, 'r') as version_file:
        version = version_file.read().strip()
except IOError:
    version = '0.0.0.dev0'
    with open(version_file_path, 'w') as version_file:
        version_file.write(version)


setuptools.setup(
    name='zazu',
    version=version,
    description='At your service for development workflow management',
    long_description=description,
    author='Nicholas Wiles',
    author_email='nic@lily.camera',
    url='https://github.com/LilyRobotics/zazu',
    license='BSD',
    packages=setuptools.find_packages(exclude=('tests', 'docs')),
    package_data={'zazu': ['cmake/*.cmake', 'githooks/*', 'version.txt']},
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
                      'futures==3.0.5',
                      'inquirer==2.1.7'],
    extras_require={
        ':sys_platform == "win32"': [
            'pyreadline==2.1'
        ],
        ':sys_platform != "win32"': [
            'gnureadline==6.3.3'
        ]
    },
    entry_points='''
        [console_scripts]
        zazu=zazu.cli:cli
        '''
)
