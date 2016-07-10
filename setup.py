# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

try:
    import pypandoc
    description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    description = ''

setup(
    name='zazu',
    version='0.0.1.dev',
    description='At your service for development workflow management',
    long_description=description,
    author='Nicholas Wiles',
    author_email='nic@lily.camera',
    url='https://github.com/LilyRobotics/zazu',
    license='BSD',
    packages=find_packages(exclude=('tests', 'docs')),
    package_data={'zazu': ['cmake/*.cmake', 'githooks/*', 'pypi/pip.conf']},
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

