# -*- coding: utf-8 -*-
import zazu.build
import zazu.git_helper
import zazu.github_helper
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'functools',
    'git',
    'os'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@click.group()
@click.pass_context
def repo(ctx):
    """Manage repository"""
    pass


@repo.group()
@click.pass_context
def setup(ctx):
    """Setup repository with services"""
    ctx.obj.check_repo()
    pass


@setup.command()
@click.pass_context
def hooks(ctx):
    """Setup default git hooks"""
    zazu.git_helper.install_git_hooks(ctx.obj.repo_root)


@setup.command()
@click.pass_context
def ci(ctx):
    """Setup CI configurations based on a zazu.yaml file"""
    ctx.obj.check_repo()
    build_server = ctx.obj.build_server()
    project_config = ctx.obj.project_config()
    if click.confirm("Post build configuration to {}?".format(build_server.type())):
        scm_url = ctx.obj.repo.remotes.origin.url
        scm_org, scm_name = zazu.github_helper.parse_github_url(scm_url)
        components = project_config['components']
        for c in components:
            component = zazu.build.ComponentConfiguration(c)
            build_server.setup_component(component, scm_name, scm_url)


@repo.command()
@click.argument('repository_url')
@click.option('--nohooks', is_flag=True, help='does not install git hooks in the cloned repo')
@click.option('--nosubmodules', is_flag=True, help='does not update submodules')
@click.pass_context
def clone(ctx, repository_url, nohooks, nosubmodules):
    """Clone and initialize a repo

        Args:
            repository_url(str):url of the repository to clone
    """
    try:
        destination = '{}/{}'.format(os.getcwd(), repository_url.rsplit('/', 1)[-1].replace('.git', ''))
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
@click.pass_context
def init(ctx):
    """Initialize repo directory structure"""
    raise NotImplementedError


@repo.command()
@click.option('-r', '--remote', is_flag=True, help='Also clean up remote branches')
@click.option('-b', '--target_branch', default='origin/master', help='Delete branches merged with this branch')
@click.pass_context
def cleanup(ctx, remote, target_branch):
    """Clean up merged branches that have been merged or are associated with closed/resolved tickets"""
    ctx.obj.check_repo()
    repo_obj = ctx.obj.repo
    try:
        repo_obj.git.checkout('develop')
    except git.exc.GitCommandError:
        raise click.ClickException('unable to checkout "develop"')
    issue_tracker = ctx.obj.issue_tracker()
    closed_branches = set([])
    if remote:
        repo_obj.git.fetch('--prune')
        remote_branches = zazu.git_helper.filter_undeletable([b.name for b in repo_obj.remotes.origin.refs])
        if issue_tracker is not None:
            closed_branches = set(get_closed_branches(issue_tracker, remote_branches))
        merged_remote_branches = zazu.git_helper.filter_undeletable(zazu.git_helper.get_merged_branches(repo_obj, target_branch, remote=True))
        merged_remote_branches = [b.replace('origin/', '') for b in merged_remote_branches]
        branches_to_delete = set(merged_remote_branches) | closed_branches
        if branches_to_delete:
            click.echo('These remote branches will be deleted: {}'.format(zazu.util.pprint_list(branches_to_delete)))
            if click.confirm('Proceed?'):
                for b in branches_to_delete:
                    click.echo('Deleting {}'.format(b))
                repo_obj.git.push('-df', 'origin', *branches_to_delete)
    merged_branches = zazu.git_helper.filter_undeletable(zazu.git_helper.get_merged_branches(repo_obj, target_branch))
    local_branches = set(zazu.git_helper.filter_undeletable([b.name for b in repo_obj.heads]))
    if issue_tracker is not None:
        branches_to_check = local_branches - closed_branches
        closed_branches |= set(get_closed_branches(issue_tracker, branches_to_check))
    branches_to_delete = (closed_branches & local_branches) | set(merged_branches)
    if branches_to_delete:
        click.echo('These local branches will be deleted:{}'.format(zazu.util.pprint_list(branches_to_delete)))
        if click.confirm('Proceed?'):
            for b in branches_to_delete:
                click.echo('Deleting {}'.format(b))
            repo_obj.git.branch('-D', *branches_to_delete)


def tickets_from_branches(branches):
    descriptors = []
    for b in branches:
        try:
            descriptors.append(zazu.dev.commands.make_issue_descriptor(b))
        except click.ClickException:
            pass
    return descriptors


def get_closed_branches(issue_tracker, branches):
    """get descriptors of branches that refer to closed branches"""
    def ticket_if_closed(tracker, ticket):
        try:
            if tracker.issue(ticket.id).closed:
                return ticket
        except zazu.issue_tracker.IssueTrackerError:
            pass
        return None

    work = [functools.partial(ticket_if_closed, issue_tracker, t) for t in tickets_from_branches(branches)]
    closed_tickets = zazu.util.dispatch(work)
    return [t.get_branch_name() for t in closed_tickets if t is not None]


def ticket_is_closed(issue_tracker, descriptor):
    """determines if a ticket is closed or not, defaults to false in case the ticket isn't found by the issue tracker"""
    try:
        return issue_tracker.issue(descriptor.id).closed
    except zazu.issue_tracker.IssueTrackerError:
        return False
