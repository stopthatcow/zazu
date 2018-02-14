# -*- coding: utf-8 -*-

"""Dev subcommand for zazu."""
import zazu.git_helper
import zazu.github_helper
import zazu.config
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'concurrent.futures',
    'git',
    'os',
    'webbrowser',
    'textwrap',
    'urllib'

])

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def description_to_branch(description):
    """Sanitizes a string for inclusion into branch name"""
    return description.replace(' ', '_')


class IssueDescriptor(object):
    """Info holder of type, ticket ID, and description"""

    def __init__(self, type, id, description=''):
        self.type = type
        self.id = id
        self.description = description

    def get_branch_name(self):
        sanitized_description = ""
        if self.description:
            sanitized_description = self.description.replace(' ', '_')
        ret = self.id
        if self.type:
            ret = '{}/{}'.format(self.type, ret)
        if self.description:
            ret = '{}_{}'.format(ret, sanitized_description)
        return ret


def make_ticket(issue_tracker):
    """Creates a new ticket interactively"""
    # ensure that we have a connection
    issue_tracker.connect()
    project = issue_tracker.default_project()
    issue_type = zazu.util.pick(issue_tracker.issue_types(), 'Pick issue type')
    component = zazu.util.pick(issue_tracker.issue_components(), 'Pick issue component')
    click.echo('Making a new {} in the "{}" project, "{}" component...'.format(issue_type.lower(), project, component))
    summary = zazu.util.prompt('Enter a title')
    description = zazu.util.prompt('Enter a description')
    issue = issue_tracker.create_issue(project, issue_type, summary, description, component)
    # Self assign the new ticket
    issue_tracker.assign_issue(issue, issue.fields.reporter.name)
    return issue


def verify_ticket_exists(issue_tracker, ticket_id):
    """Verify that a given ticket exists"""
    try:
        issue = issue_tracker.issue(ticket_id)
        click.echo("Found ticket {}: {}".format(ticket_id, issue.fields.summary))
    except zazu.issue_tracker.IssueTrackerError:
        raise click.ClickException('no ticket named "{}"'.format(ticket_id))


def offer_to_stash_changes(repo):
    """Offers to stash local changes if there are any"""
    diff = repo.index.diff(None)
    status = repo.git.status('-s', '-uno')
    if len(diff) and len(status):
        click.echo(status)
        if click.confirm('Local changes detected, stash first?', default=True):
            repo.git.stash()


def make_issue_descriptor(name):
    """Splits input into type, id and description"""
    known_types = set(['hotfix', 'release', 'feature'])
    type = None
    description = None
    if '-' not in name:
        raise click.ClickException("Branch name must be in the form PROJECT-NUMBER, type/PROJECT-NUMBER, or type/PROJECT_NUMBER_description")
    components = name.split('/')
    if len(components) > 1:
        type = components[-2]
        if type not in known_types:
            raise click.ClickException("Branch type specifier must be one of {}".format(known_types))
    components = components.pop().split('_', 1)
    if len(components) == 2:
        description = components[1]
    id = components[0]
    return IssueDescriptor(type, id, description)


@click.group()
@click.pass_context
def dev(ctx):
    """Create or update work items"""
    ctx.obj.check_repo()


def check_if_branch_is_protected(branch_name):
    """throws if branch_name is protected from being renamed"""
    protected_branches = ['develop', 'master']
    if branch_name in protected_branches:
        raise click.ClickException('branch "{}" is protected'.format(branch_name))


def check_if_active_branch_can_be_renamed(repo):
    """throws if the current head is detached or if the active branch is protected"""
    if repo.head.is_detached:
        raise click.ClickException("the current HEAD is detached")
    check_if_branch_is_protected(repo.active_branch.name)


def rename_branch(repo, old_branch, new_branch):
    """Renames old_branch in repo to new_branch, locally and remotely"""
    check_if_branch_is_protected(old_branch)
    remote_branch_exists = repo.heads[old_branch].tracking_branch() is not None
    if remote_branch_exists:
        # Pull first to avoid orphaning remote commits when we delete the remote branch
        repo.git.pull()
    repo.git.branch(['-m', new_branch])
    try:
        repo.git.push(['origin', ':{}'.format(old_branch)])
    except git.exc.GitCommandError:
        pass
    repo.git.push(['-u'])


def complete_git_branch(ctx, args, incomplete):
    """Completion fn that returns current branch list."""
    repo = git.Repo(os.getcwd())
    return zazu.git_helper.get_undeletable_branches(repo)


@dev.command()
@click.argument('name', autocompletion=complete_git_branch)
@click.pass_context
def rename(ctx, name):
    """Renames the current branch, locally and remotely"""
    repo = ctx.obj.repo
    rename_branch(repo, repo.active_branch.name, name)


@dev.command()
@click.argument('name', required=False)
@click.option('--no-verify', is_flag=True, help='Skip verification that ticket exists')
@click.option('--head', is_flag=True, help='Branch off of the current head rather than develop')
@click.option('rename_flag', '--rename', is_flag=True, help='Rename the current branch rather than making a new one')
@click.option('-t', '--type', type=click.Choice(['feature', 'release', 'hotfix']), help='the ticket type to make',
              default='feature')
@click.pass_context
def start(ctx, name, no_verify, head, rename_flag, type):
    """Start a new feature, much like git-flow but with more sugar"""
    if rename_flag:
        check_if_active_branch_can_be_renamed(ctx.obj.repo)
    if not (head or rename_flag):
        offer_to_stash_changes(ctx.obj.repo)
        click.echo('Checking out develop...')
        ctx.obj.repo.heads.develop.checkout()
        click.echo('Pulling from origin...')
        try:
            ctx.obj.repo.remotes.origin.pull()
        except git.exc.GitCommandError:
            click.secho('WARNING: unable to pull from origin!', fg='red')
    if name is None:
        try:
            name = str(make_ticket(ctx.obj.issue_tracker()))
        except zazu.issue_tracker.IssueTrackerError as e:
            raise click.ClickException(str(e))
        click.echo('Created ticket "{}"'.format(name))
    issue = make_issue_descriptor(name)
    if not no_verify:
        verify_ticket_exists(ctx.obj.issue_tracker(), issue.id)
    if issue.description is None:
        issue.description = zazu.util.prompt('Enter a short description for the branch')
    issue.type = type
    branch_name = issue.get_branch_name()
    try:
        # Check if the target branch already exists
        ctx.obj.repo.git.checkout(branch_name)
        click.echo('Branch {} already exists!'.format(branch_name))
    except git.exc.GitCommandError:
        if rename_flag:
            click.echo('Renaming current branch to "{}"...'.format(branch_name))
            rename_branch(ctx.obj.repo, ctx.obj.repo.active_branch.name, branch_name)
        else:
            click.echo('Creating new branch named "{}"...'.format(branch_name))
            ctx.obj.repo.git.checkout('HEAD', b=branch_name)


def wrap_text(text):
    return '\n'.join(['\n'.join(textwrap.wrap(line, 90, break_long_words=False, initial_indent='    ',
                                              subsequent_indent='    ')) for line in text.splitlines()])


@dev.command()
@click.pass_context
def status(ctx):
    """Get status of this branch"""
    descriptor = make_issue_descriptor(ctx.obj.repo.active_branch.name)
    issue_id = descriptor.id
    if not issue_id:
        raise click.ClickException('The current branch does not contain a ticket ID')
    else:
        gh = zazu.github_helper.make_gh()

        def get_pulls_for_branch(branch):
            org, repo = zazu.github_helper.parse_github_url(ctx.obj.repo.remotes.origin.url)
            pulls = gh.get_user(org).get_repo(repo).get_pulls()
            return [p for p in pulls if p.head.ref == branch]

        # Dispatch REST calls asynchronously
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            issue_future = executor.submit(ctx.obj.issue_tracker().issue, issue_id)
            pulls_future = executor.submit(get_pulls_for_branch, ctx.obj.repo.active_branch.name)

            click.echo(click.style('Ticket info:', bg='white', fg='black'))
            try:
                issue = issue_future.result()
                type = issue.fields.issuetype.name
                click.echo(click.style('    {} ({}): '.format(type, issue.fields.status.name), fg='green'), nl=False)
                click.echo(issue.fields.summary)
                click.echo(click.style('    Description:\n', fg='green'), nl=False)
                click.echo(wrap_text(issue.fields.description))
            except zazu.issue_tracker.IssueTrackerError:
                click.echo("    No ticket found")

            matches = pulls_future.result()
            click.secho('Pull request info:', bg='white', fg='black')
            click.echo('    {} matching PRs'.format(len(matches)))
            if matches:
                for p in matches:
                    click.echo(click.style('    PR Name:  ', fg='green') + p.title)
                    click.echo(click.style('    PR State: ', fg='green') + p.state)
                    click.echo(click.style('    PR Body:\n', fg='green') + wrap_text(p.body))

                    # TODO: build status from TC


@dev.command()
@click.pass_context
def review(ctx):
    """Create or display pull request"""
    encoded_branch = urllib.quote_plus(ctx.obj.repo.active_branch.name)
    url = ctx.obj.repo.remotes.origin.url
    start = 'github.com'
    if start in url:
        base_url = url[url.find(start):].replace('.git', '').replace(':', '/')
        url = 'https://{}/compare/{}?expand=1'.format(base_url, encoded_branch)
        click.echo('Opening "{}"'.format(url))
        webbrowser.open_new(url)
        # TODO: add link to ticket in the PR, zazu logo
        # <img src="http://vignette1.wikia.nocookie.net/disney/images/c/ca/Zazu01cf.png" alt="Zazu" width=50"/>
    else:
        raise click.UsageError("Can't open a PR for a non-github repo")


@dev.command()
@click.pass_context
@click.argument('ticket', default='')
def ticket(ctx, ticket):
    """Open the ticket for the current feature or the one supplied in the ticket argument"""
    if ticket:
        issue_id = ticket
    else:
        descriptor = make_issue_descriptor(ctx.obj.repo.active_branch.name)
        issue_id = descriptor.id
    if not issue_id:
        raise click.ClickException('The current branch does not contain a ticket ID')
    else:
        url = ctx.obj.issue_tracker().browse_url(issue_id)
        click.echo('Opening "{}"'.format(url))
        webbrowser.open_new(url)


@dev.command()
@click.pass_context
def builds(ctx):
    """Display build statuses"""
    raise NotImplementedError
