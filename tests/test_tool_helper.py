# -*- coding: utf-8 -*-
import future.utils
import os
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
