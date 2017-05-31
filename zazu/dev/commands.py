# -*- coding: utf-8 -*-
import zazu.github_helper
import zazu.config
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'concurrent.futures',
    'git',
    'webbrowser',
    'textwrap',
    'urllib'

])
__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


class IssueDescriptor(object):
    """Info holder of type, ticket ID, and description"""

    def __init__(self, type, id, description=''):
        self.type = type
        self.id = id
        self.description = description

    def get_branch_name(self):
        ret = self.id
        if self.type is not None:
            ret = '{}/{}'.format(self.type, ret)
        if self.description:
            sanitized_description = self.description.replace(' ', '_')
            ret = '{}_{}'.format(ret, sanitized_description)
        return ret

    def readable_description(self):
        return self.description.replace('_', ' ').capitalize()


def make_ticket(issue_tracker):
    """Creates a new ticket interactively"""
    # ensure that we have a connection
    issue_tracker.connect()
    return issue_tracker.create_issue(project=issue_tracker.default_project(),
                                      issue_type=zazu.util.pick(issue_tracker.issue_types(), 'Pick type'),
                                      summary=zazu.util.prompt('Enter a title'),
                                      description=zazu.util.prompt('Enter a description'),
                                      component=zazu.util.pick(issue_tracker.issue_components(), 'Pick component'))


def verify_ticket_exists(issue_tracker, ticket_id):
    """Verify that a given ticket exists"""
    try:
        issue = issue_tracker.issue(ticket_id)
        click.echo("Found ticket {}: {}".format(ticket_id, issue.name))
    except zazu.issue_tracker.IssueTrackerError:
        raise click.ClickException('no ticket for id "{}"'.format(ticket_id))


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
    known_types = set(['hotfix', 'release', 'feature', 'bug'])
    type = None
    description = ''
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
    repo.git.push(['--set-upstream', 'origin', new_branch])


@dev.command()
@click.argument('name')
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
    if not issue.description:
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
    issue_id = make_issue_descriptor(ctx.obj.repo.active_branch.name).id
    # Dispatch REST calls asynchronously
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        issue_future = executor.submit(ctx.obj.issue_tracker().issue, issue_id)
        pulls_future = executor.submit(ctx.obj.code_reviewer().review, status='all', head=ctx.obj.repo.active_branch.name)

        click.echo(click.style('Ticket info:', bg='white', fg='black'))
        try:
            issue = issue_future.result()
            type = issue.type
            click.echo('{} {}'.format(click.style('    {}: '.format(type.capitalize()), fg='green'), issue.name))
            click.echo('{} {}'.format(click.style('    Status:', fg='green'), issue.status))
            click.echo(click.style('    Description:\n', fg='green'), nl=False)
            click.echo(wrap_text(issue.description))
        except zazu.issue_tracker.IssueTrackerError:
            click.echo("    No ticket found")

        matches = pulls_future.result()
        click.secho('Review info:', bg='white', fg='black')
        click.echo('    {} matching reviews'.format(len(matches)))
        if matches:
            for p in matches:
                click.echo('{} {}'.format(click.style('    Review: '.format(type.capitalize()), fg='green'), p.name))
                click.echo('{} {}, {}'.format(click.style('    Status:', fg='green'), p.status, 'merged' if p.merged else 'unmerged'))
                click.echo('{} {} -> {}'.format(click.style('    Branches:', fg='green'), p.head, p.base))
                click.echo(click.style('    Description:\n', fg='green') + wrap_text(p.description))

                # TODO: build status from TC


@dev.command()
@click.pass_context
@click.option('--base', help='The base branch to target')
@click.option('--head', help='The head branch (defaults to current branch and origin organization)')
def review(ctx, base, head):
    """Create or display pull request"""
    code_reviewer = ctx.obj.code_reviewer()
    head = ctx.obj.repo.active_branch.name if head is None else head
    existing_reviews = code_reviewer.review(status='open', head=head, base=base)
    if existing_reviews:
        pr = zazu.util.pick(existing_reviews, 'Multiple reviews found, pick one')
    else:
        descriptor = make_issue_descriptor(head)
        issue_id = descriptor.id
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            issue_future = executor.submit(ctx.obj.issue_tracker().issue, issue_id)
            base = 'develop' if base is None else base
            click.echo('No existing review found, creating one...')
            title = zazu.util.prompt('Title', default=descriptor.readable_description())
            body = zazu.util.prompt('Summary')
            try:
                issue = issue_future.result()
            except zazu.issue_tracker.IssueTrackerError:
                issue = None
            pr = code_reviewer.create_review(title=title, base=base, head=head, body=body, issue=issue)
    click.echo('Opening "{}"'.format(pr.browse_url))
    webbrowser.open_new(pr.browse_url)


@dev.command()
@click.pass_context
@click.argument('ticket', default='')
def ticket(ctx, ticket):
    """Open the ticket for the current feature or the one supplied in the ticket argument"""
    issue_id = make_issue_descriptor(ctx.obj.repo.active_branch.name).id if not ticket else ticket
    verify_ticket_exists(ctx.obj.issue_tracker(), issue_id)
    url = ctx.obj.issue_tracker().browse_url(issue_id)
    click.echo('Opening "{}"'.format(url))
    webbrowser.open_new(url)


@dev.command()
@click.pass_context
def builds(ctx):
    """Display build statuses"""
    raise NotImplementedError
