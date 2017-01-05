# -*- coding: utf-8 -*-
"""update command for zazu"""

import click

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@click.command()
@click.pass_context
@click.option('--version', default='', help='version spec to upgrade to or empty to use the version specified in the zazu.yaml file')
def upgrade(ctx, version):
    """Upgrade Zazu using pip"""
    # TODO for now hard code lily URLs, in future lean on pip.conf for this
    required_zazu_version = ctx.obj.zazu_version_required()
    if not version:
        if required_zazu_version:
            version = '=={}'.format(required_zazu_version)
        else:
            click.echo('No version specified in zazu.yaml file, upgrading to latest')
    pip_args = ['install', '--upgrade',
                '--trusted-host', 'pypi.lily.technology',
                '--index-url', 'http://pypi.lily.technology:8080/simple', 'zazu{}'.format(version)]
    import pip
    click.echo('pip {}'.format(' '.join(pip_args)))
    ctx.exit(pip.main(pip_args))
