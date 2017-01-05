import click
import zazu.git_helper
import zazu.build
import zazu.util


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


def get_git_hub_name(url):
    name = url.rsplit('/', 1)[-1]
    name = name.replace('.git', '')
    return name


@setup.command()
@click.pass_context
def ci(ctx):
    """Setup CI configurations based on a zazu.yaml file"""
    ctx.obj.check_repo()
    continuous_integration = ctx.obj.continuous_integration()
    try:
        project_config = ctx.obj.project_config()
        if click.confirm("Post build configuration to {}?".format(continuous_integration.type())):
            scm_url = ctx.obj.repo.remotes.origin.url
            scm_name = get_git_hub_name(scm_url)
            components = project_config['components']
            for c in components:
                component = zazu.build.ComponentConfiguration(c)
                continuous_integration.setup_component(component, scm_name, scm_url)
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
    """Clean up merged branches that have been merged or are associated with cloded/resolved tickets"""
    repo_obj = ctx.obj.repo
    repo_obj.git.checkout('develop')
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
    return [t.get_branch_name() for t in tickets_from_branches(branches) if ticket_is_closed(issue_tracker, t)]


def ticket_is_closed(issue_tracker, descriptor):
    """determines if a ticket is closed or not, defaults to false in case the ticket isn't found by the issue tracker"""
    ret = False
    try:
        issue = issue_tracker.issue(descriptor.id)
        ret = issue_tracker.resolved(issue) or issue_tracker.closed(issue)
    except zazu.issue_tracker.IssueTrackerError:
        pass
    return ret
