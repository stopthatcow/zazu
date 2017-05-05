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
pytest_runner = ['pytest-runner>=2.0'] if needs_pytest else []

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
    install_requires=['click>=6.6',               # BSD
                      'requests>=2.10.0',         # Apache 2.0
                      'PyGithub>=1.26.0',         # LGPL 3
                      'jira>=1.0.10',             # BSD
                      'GitPython>=2.0.7',         # BSD
                      'pyteamcity>=0.1.1',        # MIT
                      'pyyaml>=3.11',             # MIT
                      'keyring>=8.7',             # MIT
                      'keyrings.alt>=2.2',        # MIT
                      'autopep8>=1.2.4',          # MIT
                      'semantic_version>=2.5.0',  # BSD
                      'gcovr>=3.2',               # BSD
                      'teamcity-messages>=1.19',  # Apache 2.0
                      'future>=0.16.0',           # MIT
                      'futures>=3.0.5',           # PSF
                      'inquirer>=2.1.7',          # MIT
                      'Importing>=1.10',          # PSF
                      'straight.plugin>=1.4.1'],  # MIT
    extras_require={
        ':sys_platform == "win32"': [
            'pyreadline>=2.1'                     # BSD
        ]
    },
    entry_points='''
        [console_scripts]
        zazu=zazu.cli:cli
        ''',
    setup_requires=[] + pytest_runner,
    tests_require=['pytest',
                   'pytest-cov',
                   'pytest-mock'],


)
