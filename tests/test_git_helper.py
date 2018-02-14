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


def test_get_merged_branches(git_repo):
    merged = zazu.git_helper.get_merged_branches(git_repo, 'master')
    assert merged == ['master']
    zazu.git_helper.get_merged_branches(git_repo, 'master', True)
    assert merged == ['master']


def test_git_filter_undeletable():
    some_branches = ['-', 'master', 'develop', '*current', 'HEAD', 'origin/HEAD', 'feature/foo']
    assert zazu.git_helper.filter_undeletable(some_branches) == ['feature/foo']
