# -*- coding: utf-8 -*-
"""git functions for zazu"""

import os
import filecmp
import pkg_resources
import shutil
import git

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def get_repo_root(starting_dir):
    try:
        g = git.Git(starting_dir)
        ret = g.rev_parse('--show-toplevel')
    except:
        ret = ''
    return ret


def get_hooks_path(repo_base):
    g = git.Git(repo_base)
    git_dir = g.rev_parse('--git-dir')
    return os.path.join(repo_base, git_dir, 'hooks')


def get_default_git_hooks():
    """gets list of get hooks to install"""
    return {
        "pre-commit": pkg_resources.resource_filename('zazu', 'githooks/pre-commit'),
        "post-checkout": pkg_resources.resource_filename('zazu', 'githooks/post-checkout'),
        "post-merge": pkg_resources.resource_filename('zazu', 'githooks/post-merge'),
        "commit-msg": pkg_resources.resource_filename('zazu', 'githooks/commit-msg'),
    }


def get_touched_files(repo):
    """Gets list of files that are scheduled to be committed (Added, created, modified, or renamed)"""
    return repo.git.diff('--cached', '--name-only', '--diff-filter=ACMR').split('\n')


def check_git_hooks(repo_base):
    """Checks that the default git hooks are in place"""
    have_hooks = True
    for name, file in get_default_git_hooks().items():
        if not check_git_hook(repo_base, name, file):
            have_hooks = False
            break
    return have_hooks


def check_git_hook(hooks_folder, hook_name, hook_resource_path):
    """Checks that a git hook is in place"""
    hook_path = os.path.join(hooks_folder, hook_name)
    exists = os.path.exists(hook_path)
    return exists and os.access(hook_path, os.X_OK) and filecmp.cmp(hook_path, hook_resource_path)


def install_git_hooks(repo_base):
    """Enforces that proper git hooks are in place"""
    hooks_folder = get_hooks_path(repo_base)
    for name, file in get_default_git_hooks().items():
        install_git_hook(hooks_folder, name, file)


def install_git_hook(hooks_folder, hook_name, hook_resource_path):
    """Enforces that a git hook is in place"""
    if not check_git_hook(hooks_folder, hook_name, hook_resource_path):
        try:
            os.mkdir(hooks_folder)
        except OSError:
            pass
        hook_path = os.path.join(hooks_folder, hook_name)
        shutil.copy(hook_resource_path, hook_path)


def get_merged_branches(repo, target_branch, remote=False):
    """Returns list of branches that have been merged with the target_branch"""
    args = ['--merged', target_branch]
    if remote:
        args.insert(0, '-r')
    return [b.strip() for b in repo.git.branch(args).strip().split('\n') if b]


def filter_undeletable(branches):
    """Filters out branches that we don't want to delete"""
    undeletable = set(['master', 'develop', 'origin/develop', 'origin/master', '-'])
    return [b for b in branches if (b not in undeletable) and (not b.startswith('*')) and (not b.startswith('origin/HEAD'))]


def get_undeletable_branches(repo):
    branches = [b.name for b in repo.branches]
    return filter_undeletable(branches)


def read_staged(path):
    """Read the contents of the staged version of the file."""
    return zazu.util.check_output(['git', 'show', ':{}'.format(path)])
