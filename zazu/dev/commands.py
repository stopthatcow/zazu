# -*- coding: utf-8 -*-
"""Dev subcommand for zazu."""

import zazu.imports
zazu.imports.lazy_import(locals(), [
    'click',
    'concurrent.futures',
    'git',
    'os',
    'webbrowser',
    'textwrap',
    'urllib',
    'zazu.github_helper',
    'zazu.config',
    'zazu.util',
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


class IssueDescriptor(object):
    """Info holder of type, ticket ID, and description."""

    def __init__(self, type, id, description=''):
        """Create an IssueDescriptor.

        Args:
            type (str): the issue type.
            id (str): the issue tracker id.
            description (str): a brief description (used for the branch name only).

        """
        self.type = type
        self.id = id
        self.description = description

    def get_branch_name(self):
        """Get the branch name for this issue descriptor."""
        ret = self.id
        if self.type is not None:
            ret = '{}{}'.format(self.type, ret)
        if self.description:
            sanitized_description = self.description.replace(' ', '_')
            ret = '{}_{}'.format(ret, sanitized_description)
        return ret

    def readable_description(self):
        """Get the human readable description by replacing underscores with spaces."""
        return self.description.replace('_', ' ').capitalize()


def make_ticket(issue_tracker):
    """Create a new ticket interactively."""
    # ensure that we have a connection
    issue_tracker.connect()
    return issue_tracker.create_issue(project=issue_tracker.default_project(),
                                      issue_type=zazu.util.pick(issue_tracker.issue_types(), 'Pick type'),
                                      summary=zazu.util.prompt('Enter a title'),
                                      description=zazu.util.prompt('Enter a description'),
                                      component=zazu.util.pick(issue_tracker.issue_components(), 'Pick component'))


def verify_ticket_exists(issue_tracker, ticket_id):
    """Verify that a given ticket exists."""
    try:
        issue = issue_tracker.issue(ticket_id)
        click.echo('Found ticket {}: {}'.format(issue.id, issue.name))
        return issue
    except zazu.issue_tracker.IssueTrackerError:
        raise click.ClickException('no ticket for id "{}"'.format(ticket_id))


def offer_to_stash_changes(repo):
    """Offer to stash local changes if there are any."""
    diff = repo.index.diff(None)
    status = repo.git.status('-s', '-uno')
    if diff and status:
        click.echo(status)
        if click.confirm('Local changes detected, stash first?', default=True):
            repo.git.stash()


def make_issue_descriptor(name, require_type=False):
    """Split input into type, id and description."""
    known_types = {'hotfix/', 'release/', 'feature/', 'support/'}
    type = None
    description = ''
    for t in known_types:
        if name.startswith(t):
            type = t
            name = name[len(t):]
    if type is None and require_type:
        raise click.ClickException('Branch prefix must be one of {}'.format(known_types))
    components = name.split('_', 1)
    id = components[0]
    if len(components) == 2:
        description = components[1]
    return IssueDescriptor(type, id, description)


@click.group()
@zazu.config.pass_config
def dev(config):
    """Create or update work items."""
    config.check_repo()


def check_if_branch_is_protected(branch_name):
    """Throw if branch_name is protected from being renamed."""
    protected_branches = ['develop', 'master']
    if branch_name in protected_branches:
        raise click.ClickException('branch "{}" is protected'.format(branch_name))


def check_if_active_branch_can_be_renamed(repo):
    """Throw if the current head is detached or if the active branch is protected."""
    if repo.head.is_detached:
        raise click.ClickException('the current HEAD is detached')
    check_if_branch_is_protected(repo.active_branch.name)


def rename_branch(repo, old_branch, new_branch):
    """Rename old_branch in repo to new_branch, locally and remotely."""
    check_if_branch_is_protected(old_branch)
    remote_branch_exists = repo.heads[old_branch].tracking_branch() is not None
    if remote_branch_exists:
        # Pull first to avoid orphaning remote commits when we delete the remote branch
        repo.git.pull()
    repo.git.branch('-m', new_branch)
    try:
        repo.git.push('origin', ':{}'.format(old_branch))
    except git.exc.GitCommandError:
        pass
    try:
        repo.git.push('--set-upstream', 'origin', new_branch)
    except git.exc.GitCommandError:
        pass


def complete_git_branch(ctx, args, incomplete):
    """Completion function that returns current branch list."""
    repo = git.Repo(os.getcwd())
    return sorted([b.name for b in repo.branches])


def complete_issue(ctx, args, incomplete):
    """Completion function that returns ids for open issues."""
    issues = zazu.config.Config().issue_tracker().issues()
    return sorted([(i, i.name) for i in issues if str(i).startswith(incomplete) or incomplete.lower() in i.name.lower()])


def complete_feature(ctx, args, incomplete):
    """Completion function that returns feature/<id> for open issues."""
    return sorted([('feature/{}'.format(id), description) for id, description in complete_issue(ctx, args, incomplete)])


@dev.command()
@click.argument('name', autocompletion=complete_feature)
@zazu.config.pass_config
def rename(config, name):
    """Rename the current branch, locally and remotely."""
    repo = config.repo
    check_if_active_branch_can_be_renamed(repo)
    rename_branch(repo, repo.active_branch.name, name)


def find_branch_with_id(repo, id):
    """Find a branch with a given issue id."""
    descriptors = zazu.repo.commands.descriptors_from_branches([h.name for h in repo.heads], require_type=False)
    try:
        return next(d.get_branch_name() for d in descriptors if d.id == id)
    except StopIteration:
        pass


def branch_is_current(repo, branch):
    """Return True if branch is up to date with its tracking branch or if it doesn't have a tracking branch."""
    repo.remotes.origin.fetch()
    if repo.heads[branch].tracking_branch() is None:
        return True
    return repo.git.rev_parse('{}@{{0}}'.format(branch)) == repo.git.rev_parse('{}@{{u}}'.format(branch))


@dev.command()
@click.argument('name', required=False, autocompletion=complete_issue)
@click.option('--no-verify', is_flag=True, help='Skip verification that ticket exists')
@click.option('--head', is_flag=True, help='Branch off of the current head rather than develop')
@click.option('rename_flag', '--rename', is_flag=True, help='Rename the current branch rather than making a new one')
@click.option('-t', '--type', type=click.Choice(['feature/', 'release/', 'hotfix/', 'support/']), help='the ticket type to make',
              default='feature/')
@zazu.config.pass_config
def start(config, name, no_verify, head, rename_flag, type):
    """Start a new feature, much like git-flow but with more sugar."""
    repo = config.repo
    if rename_flag:
        check_if_active_branch_can_be_renamed(repo)

    # Fetch in the background.
    develop_branch_name = config.develop_branch_name()
    if not (head or rename_flag):
        develop_is_current_future = zazu.util.async_do(branch_is_current, repo, develop_branch_name)
    if name is None:
        try:
            name = str(make_ticket(config.issue_tracker()))
            no_verify = True  # Making the ticket implicitly verifies it.
        except zazu.issue_tracker.IssueTrackerError as e:
            raise click.ClickException(str(e))
        click.echo('Created ticket "{}"'.format(name))
    issue_descriptor = make_issue_descriptor(name)
    # Sync with the background fetch process before touching the git repo.
    if not (head or rename_flag):
        try:
            develop_is_current = develop_is_current_future.result()
        except (git.exc.GitCommandError, AttributeError):
            zazu.util.warn('unable to fetch from origin!')
            develop_is_current = True
    existing_branch = find_branch_with_id(repo, issue_descriptor.id)
    if existing_branch and not (rename_flag and repo.active_branch.name == existing_branch):
        raise click.ClickException('branch with same id exists: {}'.format(existing_branch))
    issue = None if no_verify else verify_ticket_exists(config.issue_tracker(), issue_descriptor.id)
    if not issue_descriptor.description:
        issue_descriptor.description = zazu.util.prompt('Enter a short description for the branch')
    issue_descriptor.type = type
    branch_name = issue_descriptor.get_branch_name()
    if not (head or rename_flag):
        offer_to_stash_changes(repo)
        click.echo('Checking out {}...'.format(develop_branch_name))
        repo.heads[develop_branch_name].checkout()
        if not develop_is_current:
            click.echo('Merging latest from origin...')
            repo.git.merge()

    try:
        repo.git.checkout(branch_name)
        click.echo('Branch {} already exists!'.format(branch_name))
    except git.exc.GitCommandError:
        if rename_flag:
            click.echo('Renaming current branch to "{}"...'.format(branch_name))
            rename_branch(repo, repo.active_branch.name, branch_name)
        else:
            click.echo('Creating new branch named "{}"...'.format(branch_name))
            repo.git.checkout('HEAD', b=branch_name)
    if issue is not None:
        config.issue_tracker().assign_issue(issue, config.issue_tracker().user())


def wrap_text(text, width=90, indent=''):
    """Wrap each line of text to width characters wide with indent.

    Args:
        text (str): The text to wrap.
        width (str): width to wrap to.
        indent (str): the indent to prepend to each line.

    Returns:
        str: A wrapped block of text.

    """
    return '\n'.join(['\n'.join(textwrap.wrap(line, width,
                                              break_long_words=False,
                                              initial_indent=indent,
                                              subsequent_indent=indent)) for line in text.splitlines()])


@dev.command()
@click.argument('name', required=False, autocompletion=complete_issue)
@zazu.config.pass_config
def status(config, name):
    """Get status of a issue."""
    issue_id = make_issue_descriptor(config.repo.active_branch.name).id if name is None else name
    # Dispatch REST calls asynchronously
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        issue_future = executor.submit(config.issue_tracker().issue, issue_id)
        pulls_future = executor.submit(config.code_reviewer().review, status='all', head=config.repo.active_branch.name)

        click.echo(click.style('Ticket info:', bg='white', fg='black'))
        try:
            issue = issue_future.result()
            type = issue.type
            click.echo('{} {}'.format(click.style('    {}: '.format(type.capitalize()), fg='green'), issue.name))
            click.echo('{} {}'.format(click.style('    Status:', fg='green'), issue.status))
            click.echo(click.style('    Description:\n', fg='green'), nl=False)
            click.echo(wrap_text(issue.description, indent='    '))
        except zazu.issue_tracker.IssueTrackerError:
            click.echo('    No ticket found')

        matches = pulls_future.result()
        click.secho('Review info:', bg='white', fg='black')
        click.echo('    {} matching reviews'.format(len(matches)))
        if matches:
            for p in matches:
                click.echo('{} {}'.format(click.style('    Review:', fg='green'), p.name))
                click.echo('{} {}, {}'.format(click.style('    Status:', fg='green'), p.status, 'merged' if p.merged else 'unmerged'))
                click.echo('{} {} -> {}'.format(click.style('    Branches:', fg='green'), p.head, p.base))
                click.echo(click.style('    Description:\n', fg='green') + wrap_text(p.description, indent='    '))


@dev.command()
@zazu.config.pass_config
@click.option('--base', help='The base branch to target', autocompletion=complete_git_branch)
@click.option('--head', help='The head branch (defaults to current branch and origin organization)')
def review(config, base, head):
    """Create or display pull request."""
    code_reviewer = config.code_reviewer()
    head = config.repo.active_branch.name if head is None else head
    existing_reviews = code_reviewer.review(status='open', head=head, base=base)
    if existing_reviews:
        pr = zazu.util.pick(existing_reviews, 'Multiple reviews found, pick one')
    else:
        descriptor = make_issue_descriptor(head)
        status = config.repo.git.status(['--porcelain'])
        if status:
            raise click.ClickException('working tree is not clean, stash or remove changes in your repo')    
        try:
            config.repo.git.push('--set-upstream','origin', head)
        except git.exc.GitCommandError as e:
            raise click.ClickException('failed to push to origin: {}'.format(e))    
        issue_id = descriptor.id
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            issue_future = executor.submit(config.issue_tracker().issue, issue_id)
            base = config.develop_branch_name() if base is None else base
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
@zazu.config.pass_config
@click.argument('ticket', required=False, autocompletion=complete_issue)
def ticket(config, ticket):
    """Open the ticket for the current feature or the one supplied in the ticket argument."""
    issue_id = make_issue_descriptor(config.repo.active_branch.name).id if not ticket else ticket
    issue = verify_ticket_exists(config.issue_tracker(), issue_id)
    url = issue.browse_url
    click.echo('Opening "{}"'.format(url))
    webbrowser.open_new(url)
