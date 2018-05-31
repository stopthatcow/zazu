# -*- coding: utf-8 -*-

import os
import zazu.git_helper

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_repo_root(git_repo):
    root = git_repo.working_tree_dir
    assert root in zazu.git_helper.get_repo_root(root)
    assert not zazu.git_helper.get_repo_root('/')


def test_hooks(git_repo):
    dir = git_repo.working_tree_dir
    assert not zazu.git_helper.check_git_hooks(dir)
    zazu.git_helper.install_git_hooks(dir)
    assert zazu.git_helper.check_git_hooks(dir)


def test_touched_files(git_repo):
    dir = git_repo.working_tree_dir
    assert len(zazu.git_helper.get_touched_files(git_repo)) == 0
    # new file
    test_file = os.path.join(dir, 'test')
    with open(test_file, 'w') as file:
        file.write('hello')
    assert len(zazu.git_helper.get_touched_files(git_repo)) == 0
    git_repo.index.add([test_file])
    assert len(zazu.git_helper.get_touched_files(git_repo)) == 1
    # modified file
    existing = os.path.join(dir, 'README.md')
    with open(existing, 'a') as file:
        file.write('hello')
    git_repo.index.add([existing])
    assert len(zazu.git_helper.get_touched_files(git_repo)) == 2


def test_merged_branches(git_repo):
    with zazu.util.cd(git_repo.working_tree_dir):
        git_repo.create_head('foo').checkout()
        with open('test', 'w') as f:
            pass
        git_repo.index.add(['test'])
        git_repo.index.commit('commit')
        git_repo.git.checkout('master')
        merged = zazu.git_helper.merged_branches(git_repo, 'master')
        assert not merged
        git_repo.git.merge('foo')
        merged = zazu.git_helper.merged_branches(git_repo, 'master')
        assert merged == {'foo'}
        zazu.git_helper.merged_branches(git_repo, 'master', True)
        assert merged == {'foo'}
