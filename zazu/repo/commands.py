# -*- coding: utf-8 -*-
"""Holds the zazu repo subcommand."""
import zazu.git_helper
import zazu.github_helper
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'functools',
    'git',
    'os',
    'socket'
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


@click.group()
@click.pass_context
def repo(ctx):
    """Manage repository."""
    pass


@repo.command()
@click.pass_context
def init(ctx):
    """Install git hooks to repo."""
    ctx.obj.check_repo()
    zazu.git_helper.install_git_hooks(ctx.obj.repo_root)


@repo.command()
@click.argument('repository')
@click.argument('destination', required=False)
@click.option('--nohooks', is_flag=True, help='does not install git hooks in the cloned repo')
@click.option('--nosubmodules', is_flag=True, help='does not update submodules')
@click.pass_context
def clone(ctx, repository, destination, nohooks, nosubmodules):
    """Clone and initialize a repo.

    Args:
        repository (str): name or url of the repository to clone.
        destination (str): path to clone the repo to.
        nohooks (bool): if True, git hooks are not installed.
        nosubmodules (bool): if True submodules are not initialized.
    """
    if os.path.isdir(repository) or ':' in repository:
        repository_url = repository
    elif ctx.obj.scm_hosts():
        scm_repo = ctx.obj.scm_host_repo(repository)
        if scm_repo is None:
            raise click.ClickException('Unable to find hosted SCM repo {}'.format(repository))
        repository_url = scm_repo.ssh_url
    else:
        raise click.ClickException('Unable to clone {}'.format(repository))

    if destination is None:
        destination = repository_url.rsplit('/', 1)[-1].replace('.git', '')
    click.echo('Cloning {} into {}'.format(repository_url, destination))

    try:
        repo = git.Repo.clone_from(repository_url, destination)
        click.echo('Repository successfully cloned')

        if not nohooks:
            click.echo('Installing Git Hooks')
            zazu.git_helper.install_git_hooks(repo.working_dir)

        if not nosubmodules:
            click.echo('Updating all submodules')
            repo.submodule_update(init=True, recursive=True)

    except git.GitCommandError as err:
        raise click.ClickException(str(err))


@repo.command()
@click.option('-r', '--remote', is_flag=True, help='Also clean up remote branches')
@click.option('-b', '--target_branch', default='origin/master', help='Delete branches merged with this branch')
@click.option('-y', '--yes', is_flag=True, help='Don\'t ask to before deleting branches')
@click.pass_context
def cleanup(ctx, remote, target_branch, yes):
    """Clean up merged branches that have been merged or are associated with closed/resolved tickets."""
    ctx.obj.check_repo()
    repo_obj = ctx.obj.repo
    develop_branch_name = ctx.obj.develop_branch_name()
    try:
        repo_obj.heads[develop_branch_name].checkout()
    except IndexError:
        raise click.ClickException('unable to checkout "{}"'.format(develop_branch_name))
    try:
        issue_tracker = ctx.obj.issue_tracker()
    except click.ClickException:
        issue_tracker = None
    closed_branches = set()
    protected_branches = ctx.obj.protected_branches()
    protected_remote_branches = {'origin/{}'.format(b) for b in protected_branches}
    if remote:
        repo_obj.git.fetch('--prune')
        remote_branches = {b.name for b in repo_obj.remotes.origin.refs} - protected_remote_branches
        remote_branch_names = {b.replace('origin/', '') for b in remote_branches}
        if issue_tracker is not None:
            closed_branches = get_closed_branches(issue_tracker, remote_branch_names)
        merged_remote_branches = zazu.git_helper.merged_branches(repo_obj, target_branch, remote=True)
        empty_branches = {b for b in remote_branches if branch_is_empty(repo_obj, b, 'origin/{}'.format(develop_branch_name))}
        branches_to_delete = (merged_remote_branches | closed_branches | empty_branches) - protected_remote_branches
        branches_to_delete = {b.replace('origin/', '') for b in branches_to_delete}
        if branches_to_delete:
            confirmation = 'These remote branches will be deleted: {} Proceed?'.format(zazu.util.pprint_list(branches_to_delete))
            if yes or click.confirm(confirmation):
                for b in branches_to_delete:
                    click.echo('Deleting {}'.format(b))
                repo_obj.git.push('-df', 'origin', *branches_to_delete)
    merged_branches = zazu.git_helper.merged_branches(repo_obj, target_branch) - protected_branches
    local_branches = {b.name for b in repo_obj.heads} - protected_branches
    if issue_tracker is not None:
        branches_to_check = local_branches - closed_branches
        closed_branches |= get_closed_branches(issue_tracker, branches_to_check)
    empty_branches = {b for b in local_branches if branch_is_empty(repo_obj, b, develop_branch_name)}
    branches_to_delete = ((closed_branches & local_branches) | merged_branches | empty_branches) - protected_branches
    if branches_to_delete:
        confirmation = 'These local branches will be deleted: {}\n Proceed?'.format(zazu.util.pprint_list(branches_to_delete))
        if yes or click.confirm(confirmation):
            for b in branches_to_delete:
                click.echo('Deleting {}'.format(b))
            repo_obj.git.branch('-D', *branches_to_delete)


def descriptors_from_branches(branches, require_type=False):
    """Generate IssueDescriptors from a branch names."""
    for b in branches:
        try:
            yield zazu.dev.commands.make_issue_descriptor(b, require_type)
        except click.ClickException:
            pass


def get_closed_branches(issue_tracker, branches):
    """Get descriptors of branches that refer to closed branches."""
    def descriptor_if_closed(descriptor):
        return descriptor if ticket_is_closed(issue_tracker, descriptor) else None

    work = [functools.partial(descriptor_if_closed, d) for d in descriptors_from_branches(branches)]
    closed_tickets = zazu.util.dispatch(work)
    return {t.get_branch_name() for t in closed_tickets if t is not None}


def ticket_is_closed(issue_tracker, descriptor):
    """Determine if a ticket is closed or not, defaults to False in case the ticket isn't found by the issue tracker."""
    try:
        return issue_tracker.issue(descriptor.id).closed
    except zazu.issue_tracker.IssueTrackerError:
        return False


def branch_is_empty(repo, branch, base_branch):
    """Returns True if branch has no commits newer than base_branch"""
    try:
        return int(repo.git.rev_list('--count', branch, '^{}'.format(base_branch))) == 0
    except git.GitCommandError:
        return False
