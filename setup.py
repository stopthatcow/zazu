# -*- coding: utf-8 -*-

import setuptools
import os.path
import sys

root_path = os.path.dirname(os.path.abspath(__file__))
version_file_path = os.path.join(root_path, 'zazu', 'version.txt')

with open('README.rst', 'r') as f:
    description = f.read()

# Generate PEP-440 version string. This requires zazu dependencies i.e. zazu needs to already be installed.
try:
    sys.path.insert(0, os.path.abspath('.'))
    import zazu.repo.commands
    semver = zazu.repo.commands.make_semver('.')
    version = zazu.repo.commands.pep440_from_semver(semver)
except ImportError:
    # Missing dependencies at this point.
    version = '0.0.0'

with open(version_file_path, 'w') as version_file:
    version_file.write(version)

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner>=2.0'] if needs_pytest else []

setuptools.setup(
    name='zazu',
    version=version,
    description='A development workflow management CLI for GitHub and JIRA',
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
    keywords='jira, git, github',
    packages=setuptools.find_packages(exclude=('tests', 'docs')),
    package_data={'zazu': ['githooks/*', 'version.txt']},
    install_requires=['click>=7.0',                    # BSD
                      'PyGithub>=1.36.0',              # LGPL 3
                      'jira>=1.0.11',                  # BSD
                      'GitPython>=2.1.8',              # BSD
                      'dict-recursive-update>=1.0.1',  # MIT
                      'ruamel.yaml<=0.15',             # MIT
                      'keyring<=8.0',                  # MIT
                      'keyrings.alt>=2.3',             # MIT
                      'autopep8>=1.3.4',               # MIT
                      'docformatter>=1.0',             # Expat
                      'semantic_version>=2.6.0',       # BSD
                      'future>=0.16.0',                # MIT
                      'futures>=3.2.0; python_version == "2.7"',  # PSF
                      'inquirer>=2.2.0',               # MIT
                      'Importing>=1.10',               # PSF
                      'straight.plugin>=1.5.0'],       # MIT
    extras_require={
        ':sys_platform == "win32"': [
            'pyreadline>=2.1'                          # BSD
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
