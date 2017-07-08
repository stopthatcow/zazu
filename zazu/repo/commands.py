# -*- coding: utf-8 -*-
"""Holds the zazu repo subcommand."""
import zazu.build
import zazu.git_helper
import zazu.github_helper
import zazu.util
import zazu.config
import zazu.plugins
zazu.util.lazy_import(locals(), [
    'click',
    'functools',
    'git',
    'os',
    'yaml',
    'requests'
])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


@click.group()
@click.pass_context
def repo(ctx):
    """Manage repository."""
    pass


@repo.group()
@click.pass_context
def setup(ctx):
    """Handle repository services setup."""
    ctx.obj.check_repo()
    pass


@setup.command()
@click.pass_context
def hooks(ctx):
    """Install default git hooks."""
    zazu.git_helper.install_git_hooks(ctx.obj.repo_root)


@setup.command()
@click.pass_context
def ci(ctx):
    """Post CI configurations to the CI server based on a zazu.yaml file."""
    ctx.obj.check_repo()
    build_server = ctx.obj.build_server()
    project_config = ctx.obj.project_config()
    if click.confirm("Post build configuration to {}?".format(build_server.type())):
        scm_url = ctx.obj.repo.remotes.origin.url
        _, scm_name = zazu.github_helper.parse_github_url(scm_url)
        components = project_config['components']
        for c in components:
            component = zazu.build.ComponentConfiguration(c)
            build_server.setup_component(component, scm_name, scm_url)


@repo.command()
@click.argument('repository_url')
@click.option('--nohooks', is_flag=True, help='does not install git hooks in the cloned repo')
@click.option('--nosubmodules', is_flag=True, help='does not update submodules')
def clone(repository_url, nohooks, nosubmodules):
    """Clone and initialize a repo.

    Args:
        repository_url (str): url of the repository to clone.
        nohooks (bool): if True, git hooks are not installed.
        nosubmodules (bool): if True submodules are not initialized.
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
@click.option('--nohooks', is_flag=True, help='does not install git hooks in the repo')
@click.pass_context
def init(ctx, nohooks):
    """Initialize repo directory structure"""
    def _zazu_yaml(issue_tracker={}, stylers=[]):
        """builds zazu.yaml file"""
        if issue_tracker:
            zazu_yaml_obj = issue_tracker
        else:
            zazu_yaml_obj = {}
        if stylers:
            zazu_yaml_obj['style'] = {key: {'options': ' '} for key in stylers}
            click.echo('Reminder: please specify styler options in  zazu.yaml')
        yaml.dump(zazu_yaml_obj, file('zazu.yaml', 'w'), default_flow_style=False)
    # check for git repo in cwd
    try:
        repo = git.Repo(os.getcwd())
    except git.InvalidGitRepositoryError:
        repo_name = click.prompt('No existing git repo found, Name your new repo:')

        try:
            os.mkdir(repo_name)
            repo = git.Repo.init('{}/{}/.'.format(repo_name, '.git'), bare=True)
            os.chdir(repo_name)
        except OSError as err:
            raise click.ClickException(str(err))

    if click.confirm("Configure zazu.yaml?", abort=True):
        click.echo("Configuring Zazu for: " + os.getcwd())
        if os.path.isfile('zazu.yaml'):
            click.confirm('zazu.yaml file found, continuing will overwrite, continue?', abort=True)
        repo_name = os.path.basename(os.path.normpath(os.getcwd()))

        trackers = zazu.util.get_plugin_list(zazu.issue_tracker.IssueTracker)
        trackers.append('None')
        stylers = zazu.util.get_plugin_list(zazu.styler.Styler)
        tracker_choice = zazu.util.pick(trackers, 'Pick an Issue Tracker')
        tracker_dict = {}
        if tracker_choice is not 'None':
            owner = click.prompt('Please enter an owner for issues created from this repo')
            tracker_dict['issueTracker'] = {'owner': owner, 'repo': repo_name, 'type': tracker_choice}
        styler_choice = zazu.util.pick_multiple(stylers, 'Pick some stylers')
        if not styler_choice and tracker_choice is 'None':
            click.clear()
            click.echo('No issue tracker or stylers chosen, exiting')
            exit()
        _zazu_yaml(tracker_dict, styler_choice)
        if not nohooks:
            click.echo('Installing Git Hooks')
            zazu.git_helper.install_git_hooks(repo.working_dir)
        click.echo('Creating zazu.yaml')


@repo.command()
@click.option('-r', '--remote', is_flag=True, help='Also clean up remote branches')
@click.option('-b', '--target_branch', default='origin/master', help='Delete branches merged with this branch')
@click.option('-y', '--yes', is_flag=True, help='Don\'t ask to before deleting branches')
@click.pass_context
def cleanup(ctx, remote, target_branch, yes):
    """Clean up merged branches that have been merged or are associated with closed/resolved tickets."""
    ctx.obj.check_repo()
    repo_obj = ctx.obj.repo
    try:
        repo_obj.git.checkout('develop')
    except git.exc.GitCommandError:
        raise click.ClickException('unable to checkout "develop"')
    try:
        issue_tracker = ctx.obj.issue_tracker()
    except click.ClickException:
        issue_tracker = None
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
            confirmation = 'These remote branches will be deleted: {} Proceed?'.format(zazu.util.pprint_list(branches_to_delete))
            if yes or click.confirm(confirmation):
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
        confirmation = 'These local branches will be deleted: {}\n Proceed?'.format(zazu.util.pprint_list(branches_to_delete))
        if yes or click.confirm(confirmation):
            for b in branches_to_delete:
                click.echo('Deleting {}'.format(b))
            repo_obj.git.branch('-D', *branches_to_delete)


def descriptors_from_branches(branches):
    """Generate IssueDescriptors from a branch names."""
    for b in branches:
        try:
            yield zazu.dev.commands.make_issue_descriptor(b)
        except click.ClickException:
            pass


def get_closed_branches(issue_tracker, branches):
    """Get descriptors of branches that refer to closed branches."""
    def descriptor_if_closed(tracker, descriptor):
        return descriptor if ticket_is_closed(issue_tracker, descriptor) else None

    work = [functools.partial(descriptor_if_closed, issue_tracker, d) for d in descriptors_from_branches(branches)]
    closed_tickets = zazu.util.dispatch(work)
    return [t.get_branch_name() for t in closed_tickets if t is not None]


def ticket_is_closed(issue_tracker, descriptor):
    """Determine if a ticket is closed or not, defaults to False in case the ticket isn't found by the issue tracker."""
    try:
        return issue_tracker.issue(descriptor.id).closed
    except zazu.issue_tracker.IssueTrackerError:
        return False
