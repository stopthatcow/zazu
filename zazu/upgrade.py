# -*- coding: utf-8 -*-
"""update command for zazu"""
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'pip'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@click.command()
@click.pass_context
@click.option('--version', default='', help='version spec to upgrade to or empty to use the version specified in the zazu.yaml file')
def upgrade(ctx, version):
    """Upgrade Zazu using pip"""
    required_zazu_version = ctx.obj.zazu_version_required()
    if not version:
        if required_zazu_version:
            version = '=={}'.format(required_zazu_version)
        else:
            click.echo('No version specified in zazu.yaml file, upgrading to latest')
    pip_args = ['install', '--upgrade', 'zazu{}'.format(version)]
    click.echo('pip {}'.format(' '.join(pip_args)))
    ctx.exit(pip.main(pip_args))
