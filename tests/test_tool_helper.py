# -*- coding: utf-8 -*-
import click
import future.utils
import os
import pytest
import zazu.tool.tool_helper

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_tool(git_repo, monkeypatch):
    dir = git_repo.working_tree_dir
    zazu.tool.tool_helper.package_path = os.path.join(dir, '.zazu')
    monkeypatch.setattr('zazu.tool.tool_helper.download_extract_tar_to_folder', lambda x, y, z: None)
    for tool, versions in future.utils.iteritems(zazu.tool.tool_helper.get_tool_registry()):
        for ver in versions:
            enforcer = zazu.tool.tool_helper.get_enforcer(tool, ver)
            assert not enforcer.check()
            zazu.tool.tool_helper.install_spec('{}=={}'.format(tool, ver))
            assert enforcer.check()
            zazu.tool.tool_helper.uninstall_spec('{}=={}'.format(tool, ver))
            assert not enforcer.check()


def test_parse_install_spec():
    name, ver = zazu.tool.tool_helper.parse_install_spec('foo==1.2.3')
    assert name == 'foo'
    assert ver == '1.2.3'


def test_get_enforcer():
    with pytest.raises(click.ClickException):
        zazu.tool.tool_helper.get_enforcer('gcc-arm-none-eabi', '1.0')


def test_ensure_directory_exists(tmp_dir):
    path = os.path.join(tmp_dir, 'foo')
    assert not os.path.isdir(path)
    zazu.tool.tool_helper.ensure_directory_exists(path)
    assert os.path.isdir(path)
    zazu.tool.tool_helper.ensure_directory_exists(path)
    assert os.path.isdir(path)
