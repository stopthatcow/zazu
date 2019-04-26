# -*- coding: utf-8 -*-
"""Update command for zazu."""
import zazu.imports
zazu.imports.lazy_import(locals(), [
    'click',
    'subprocess',
    'sys'
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2018'


@click.command()
@zazu.config.pass_config
@click.option('--version', default='', help='version spec to upgrade to or empty to use the version specified in the zazu.yaml file')
def upgrade(config, version):
    """Upgrade Zazu using pip."""
    required_zazu_version = config.zazu_version_required()
    if not version:
        if required_zazu_version:
            version = '=={}'.format(required_zazu_version)
        else:
            click.echo('No version specified in zazu.yaml file, upgrading to latest')
    pip_args = ['pip', 'install', '--upgrade', 'zazu{}'.format(version)]
    click.echo(' '.join(pip_args))
    sys.exit(subprocess.call(pip_args))
