# -*- coding: utf-8 -*-
import click.testing
import os
import subprocess
import pytest
import ruamel.yaml as yaml
import zazu.cli
import zazu.util

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@pytest.fixture()
def config_with_required_zazu(git_repo):
    root = git_repo.working_tree_dir
    zazu_version_config = {
        'zazu': '1.2.3'
    }
    with open(os.path.join(root, 'zazu.yaml'), 'a') as file:
        yaml.dump(zazu_version_config, file)
    return git_repo


@pytest.fixture()
def patched_subprocess_call(mocker):
    mocker.patch.object(subprocess, 'call', return_value=0, autospec=True)


def test_upgrade(patched_subprocess_call):
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['upgrade'])
    assert result.exit_code == 0
    subprocess.call.assert_called_once_with(['pip', 'install', '--upgrade', 'zazu'])


def test_upgrade_specific_version(patched_subprocess_call):
    runner = click.testing.CliRunner()
    result = runner.invoke(zazu.cli.cli, ['upgrade', '--version', '==1.2.3'])
    assert result.exit_code == 0
    subprocess.call.assert_called_once_with(['pip', 'install', '--upgrade', 'zazu==1.2.3'])


def test_upgrade_specific_version_from_config(patched_subprocess_call, config_with_required_zazu):
    with zazu.util.cd(config_with_required_zazu.working_tree_dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['upgrade'])
        assert result.exit_code == 0
        subprocess.call.assert_called_once_with(['pip', 'install', '--upgrade', 'zazu==1.2.3'])
