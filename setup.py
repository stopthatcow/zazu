# -*- coding: utf-8 -*-

import setuptools
import os.path
import sys

root_path = os.path.dirname(os.path.abspath(__file__))
version_file_path = os.path.join(root_path, 'zazu', 'version.txt')

with open('README.rst', 'r') as f:
    description = f.read()

try:
    with open(version_file_path, 'r') as version_file:
        version = version_file.read().strip()
except IOError:
    version = '0.0.0.dev0'
    with open(version_file_path, 'w') as version_file:
        version_file.write(version)

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner==2.11.1'] if needs_pytest else []

setuptools.setup(
    name='zazu',
    version=version,
    description='A development workflow management CLI for GitHub, Jira, and TeamCity',
    long_description=description,
    author='Nicholas Wiles',
    author_email='nhwiles@gmail.com',
    url='https://github.com/stopthatcow/zazu',
    license='MIT',
    platforms='POSIX,MacOS,Windows',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Quality Assurance',
        'Intended Audience :: Developers'
    ],
    keywords='teamcity, jira, git, github',
    packages=setuptools.find_packages(exclude=('tests', 'docs')),
    package_data={'zazu': ['cmake/*.cmake', 'githooks/*', 'version.txt']},
    install_requires=['click==6.6',
                      'requests==2.10.0',
                      'PyGithub==1.26.0',
                      'jira==1.0.7.dev20160607111203',
                      'GitPython==2.0.7',
                      'pyteamcity==0.1.1',
                      'pyyaml==3.11',
                      'keyring==8.7',
                      'autopep8==1.2.4',
                      'semantic_version==2.5.0',
                      'gcovr==3.2',
                      'teamcity-messages==1.19',
                      'futures==3.0.5',
                      'inquirer==2.1.7',
                      'straight.plugin==1.4.1'],
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
        ''',
    setup_requires=[]+pytest_runner,
    tests_require=['pytest-cov==2.4.0',
                   'pytest-mock==1.6.0',
                   'pytest==3.0.7'],


)
