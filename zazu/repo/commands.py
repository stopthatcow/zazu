# -*- coding: utf-8 -*-
import zazu.build
import zazu.git_helper
import zazu.github_helper
import zazu.util
import zazu.config
import zazu.plugins
import inquirer
import straight
zazu.util.lazy_import(locals(), [
    'click',
    'functools',
    'git',
    'os',
    'time',
    'socket',
    'yaml',
    'requests'
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
    continuous_integration = ctx.obj.continuous_integration()
    project_config = ctx.obj.project_config()
    if click.confirm("Post build configuration to {}?".format(continuous_integration.type())):
        scm_url = ctx.obj.repo.remotes.origin.url
        scm_org, scm_name = zazu.github_helper.parse_github_url(scm_url)
        components = project_config['components']
        for c in components:
            component = zazu.build.ComponentConfiguration(c)
            continuous_integration.setup_component(component, scm_name, scm_url)


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
@click.option('--nohooks', is_flag=True, help='does not install git hooks in the cloned repo')
@click.pass_context
def init(ctx, nohooks):
    """Initialize repo directory structure
    TODo:
    -if not git repo offer to make one
    -if git repo, assume user wants current repo to use zazu
    """

    def _zazu_yaml(issue_tracker={}, stylers=[]):
        """builds zazu.yaml file"""
        zazu_yaml_obj = issue_tracker
        if stylers:
            zazu_yaml_obj['style'] = {key: {'options':[]} for key in stylers}
        yaml.dump(zazu_yaml_obj, file('zazu.yaml','w'), default_flow_style=False)

    def _getZazuYaml():
        """gets zazu's yaml"""
        zazu_yaml = requests.get('https://raw.githubusercontent.com/stopthatcow/zazu/develop/zazu.yaml')

    # check for git repo in cwd
    try:
        repo_name = git.Repo(os.getcwd())
    except git.InvalidGitRepositoryError:
        event_time = time.gmtime()
        default_name = time.mktime(event_time)
        # click.prompt does not play well with py format
        repo_name = click.prompt('No existing git repo found, Name your new repo:', default='zazuRepoCreated_'+str(default_name))

        try:
            os.mkdir(repo_name)
            bare_repo = git.Repo.init('{}/{}/.'.format(repo_name, '.git'),bare=True)
            os.chdir(repo_name)
        except OSError as err:
            raise click.ClickException(str(err))

    if click.confirm("We are currently in a git repo, configure zazu.yaml?", abort=True):
        click.echo("Configuring Zazu for: " + os.getcwd())
        repo_name = os.path.basename(os.path.normpath(os.getcwd()))

        click.echo('Interactive Repo Design, by zazu')
        trackers = zazu.util.get_plugin_list(zazu.issue_tracker.IssueTracker)
        trackers.append('None')
        stylers = zazu.util.get_plugin_list(zazu.styler.Styler)
        tracker_choice = zazu.util.pick(trackers, 'Pick an Issue Tracker')
        if not tracker_choice is 'None':
            owner = click.prompt('Please enter an owner for issues created from this repo', default=socket.getfqdn())
            tracker_dict = {}
            tracker_dict['issueTracker'] = {'owner':owner,'repo':repo_name,'type':tracker_choice}

        styler_choice = zazu.util.pick(stylers, 'Pick some stylers', checkbox=True)
        _zazu_yaml(tracker_dict, styler_choice)
        if not nohooks:
            click.echo('Installing Git Hooks')
            zazu.git_helper.install_git_hooks(repo.working_dir)
        click.echo('Creating zazu.yaml')
 
 
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
