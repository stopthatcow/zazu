# -*- coding: utf-8 -*-
"""Git functions for zazu."""
import zazu.imports
zazu.imports.lazy_import(locals(), [
    'filecmp',
    'git',
    'os',
    'pkg_resources',
    'shutil',
    'zazu.util',
])


__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


def get_repo_root(starting_dir):
    """Get the root directory of the git repo."""
    try:
        repo = git.Repo(starting_dir, search_parent_directories=True)
        return repo.working_tree_dir
    except git.exc.InvalidGitRepositoryError:
        return None


def get_hooks_path(repo_base):
    """Get the path for git hooks."""
    g = git.Git(repo_base)
    git_dir = g.rev_parse('--git-dir')
    return os.path.join(repo_base, git_dir, 'hooks')


def get_default_git_hooks():
    """Get list of known git hooks to install."""
    return {
        'pre-commit': pkg_resources.resource_filename('zazu', 'githooks/pre-commit'),
        'post-checkout': pkg_resources.resource_filename('zazu', 'githooks/post-checkout'),
        'post-merge': pkg_resources.resource_filename('zazu', 'githooks/post-merge'),
        'commit-msg': pkg_resources.resource_filename('zazu', 'githooks/commit-msg'),
    }


def get_touched_files(repo):
    """Get list of files that are scheduled to be committed (Added, created, modified, or renamed)."""
    return [file for file in repo.git.diff('--cached', '--name-only', '--diff-filter=ACMR').split('\n') if file]


def check_git_hooks(repo_base):
    """Check that all known git hooks are in place."""
    have_hooks = True
    hooks_folder = get_hooks_path(repo_base)
    for name, file in get_default_git_hooks().items():
        if not check_git_hook(hooks_folder, name, file):
            have_hooks = False
            break
    return have_hooks


def check_git_hook(hooks_folder, hook_name, hook_resource_path):
    """Check that a git hook is in place."""
    hook_path = os.path.join(hooks_folder, hook_name)
    exists = os.path.exists(hook_path)
    return exists and os.access(hook_path, os.X_OK) and filecmp.cmp(hook_path, hook_resource_path)


def install_git_hooks(repo_base):
    """Enforce that all known git hooks are in place."""
    hooks_folder = get_hooks_path(repo_base)
    for name, file in get_default_git_hooks().items():
        install_git_hook(hooks_folder, name, file)


def install_git_hook(hooks_folder, hook_name, hook_resource_path):
    """Enforce that a git hook is in place."""
    if not check_git_hook(hooks_folder, hook_name, hook_resource_path):
        try:
            os.mkdir(hooks_folder)
        except OSError:
            pass
        hook_path = os.path.join(hooks_folder, hook_name)
        shutil.copy(hook_resource_path, hook_path)


def merged_branches(repo, target_branch, remote=False):
    """Return set of branches that have been merged with the target_branch."""
    args = ['--merged', target_branch]
    if remote:
        args.insert(0, '-r')
    return {b.strip() for b in repo.git.branch(args).strip().split('\n') if b and not b.startswith('*')}


def read_staged(path):
    """Read the contents of the staged version of the file."""
    return zazu.util.check_output(['git', 'show', ':{}'.format(path)], universal_newlines=True)
