# -*- coding: utf-8 -*-
"""update command for zazu"""

import click
import pip


@click.command()
@click.option('--version', default='', help='version spec to upgrade to or empty for latest e.g. use ==x.y.z')
def upgrade(version):
    """Upgrade Zazu using pip"""
    # TODO for now hard code lily URLs, in future lean on pip.conf for this
    return pip.main(['install', '--upgrade',
                     '--trusted-host', 'pypi.lily.technology',
                     '--index-url', 'http://pypi.lily.technology:8080/simple', 'zazu{}'.format(version)])
