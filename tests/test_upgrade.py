# -*- coding: utf-8 -*-
import click.testing
import os
import pip
import pytest
import yaml
import zazu.cli

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@pytest.fixture()
def config_with_required_zazu(git_repo):
    root = git_repo.working_tree_dir
    zazu_version_config = {
        'zazu': '1.2.3'
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        file.write(yaml.dump(zazu_version_config))
    return git_repo


@pytest.fixture()
def patched_pip_main(mocker):
    mocker.patch.object(pip, 'main', return_value=0, autospec=True)


def test_upgrade(patched_pip_main):
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['upgrade'])
    assert result.exit_code == 0
    pip.main.assert_called_once_with(['install', '--upgrade', 'zazu'])


def test_upgrade_specific_version(patched_pip_main):
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['upgrade', '--version', '==1.2.3'])
    assert result.exit_code == 0
    pip.main.assert_called_once_with(['install', '--upgrade', 'zazu==1.2.3'])


def test_upgrade_specific_version_from_config(patched_pip_main, config_with_required_zazu):
    cdw = os.getcwd()
    os.chdir(config_with_required_zazu.working_tree_dir)
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['upgrade'])
    assert result.exit_code == 0
    pip.main.assert_called_once_with(['install', '--upgrade', 'zazu==1.2.3'])
    os.chdir(cdw)
