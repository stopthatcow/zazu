import click
import zazu.teamcity_helper
import zazu.git_helper
import zazu.build
import concurrent
import multiprocessing


@click.group()
@click.pass_context
def repo(ctx):
    """Manage repository"""
    ctx.obj.check_repo()


@repo.group()
def setup():
    """Setup repository with services"""
    pass


@setup.command()
@click.pass_context
def hooks(ctx):
    """Setup default git hooks"""
    zazu.git_helper.install_git_hooks(ctx.obj.repo_root)


@setup.command()
@click.pass_context
def ci(ctx):
    """Setup TeamCity configurations based on a zazu.yaml file"""
    address = 'teamcity.lily.technology'
    port = 8111
    ctx.obj.check_repo()
    ctx.obj._tc = zazu.teamcity_helper.make_tc(address, port)
    try:
        project_config = ctx.obj.project_config()
        if click.confirm("Post build configuration to TeamCity?"):
            components = project_config['components']
            for c in components:
                component = zazu.build.ComponentConfiguration(c)
                zazu.teamcity_helper.setup(ctx.obj._tc, component, ctx.obj.repo_root)
    except IOError:
        raise click.ClickException("No {} file found in {}".format(project_file_name, ctx.obj.repo_root))


@repo.command()
@click.pass_context
def clone(ctx):
    """Clone and initialize a repo"""
    raise NotImplementedError


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
    """Clean up merged branches"""

    def filter_undeletable(branches):
        """Filters out branches that we don't want to delete"""
        undeletable = set(['master', 'develop', 'origin/develop', 'origin/master', '-'])
        return [b for b in branches if (b not in undeletable) and (not b.startswith('*')) and (b != target_branch) and (not b.startswith('origin/HEAD'))]
    repo_obj = ctx.obj.repo
    repo_obj.git.checkout('develop')
    if remote:
        repo_obj.git.fetch('--prune')
        merged_remote_branches = filter_undeletable(zazu.git_helper.get_merged_branches(repo_obj, target_branch, remote=True))
        branches_to_delete = merged_remote_branches
        if branches_to_delete:
            click.echo('The following remote branches will be deleted:')
            for b in branches_to_delete:
                click.echo('    - {}'.format(b))
            if click.confirm('Proceed?'):
                for b in branches_to_delete:
                    click.echo('Deleting {}'.format(b))
                local_branch_names = [b.replace('origin/', '') for b in branches_to_delete]
                repo_obj.git.push('-df', 'origin', *local_branch_names)
    merged_branches = filter_undeletable(zazu.git_helper.get_merged_branches(repo_obj, target_branch))
    branches = filter_undeletable([b.name for b in repo_obj.heads])
    issue_tracker = ctx.obj.issue_tracker()
    closed_branches = []
    if issue_tracker is not None:
        closed_branches = [ticket.get_branch_name() for ticket in get_closed_branches(issue_tracker, branches)]
    branches_to_delete = closed_branches + merged_branches
    if branches_to_delete:
        click.echo('The following local branches will be deleted:')
        for b in branches_to_delete:
            click.echo('    - {}'.format(b))
        if click.confirm('Proceed?'):
            for b in branches_to_delete:
                click.echo('Deleting {}'.format(b))
            repo_obj.git.branch('-D', *branches_to_delete)


def tickets_from_branches(branches):
    descriptors = []
    for b in branches:
        try:
            descriptors.append(zazu.dev.commands.make_issue_descriptor(b))
        except Exception:
            pass
    return descriptors


def get_closed_branches(issue_tracker, branches):
    """get descriptors of branches that refer to closed branches"""
    closed_tickets = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = {executor.submit(ticket_is_closed, issue_tracker, d): d for d in tickets_from_branches(branches)}
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        if result is not None:
            closed_tickets.append(result)
    return closed_tickets


def closed(ticket):
    return ticket.state == 'closed'


def ticket_is_closed(issue_tracker, descriptor):
    ticket = issue_tracker.issue(descriptor.id)
    if closed(ticket):
        ret = descriptor
    else:
        ret = None
    return ret
