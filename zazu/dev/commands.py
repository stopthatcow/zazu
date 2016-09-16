
import click
import concurrent.futures
import jira
import webbrowser
import urllib
import textwrap
import git
from zazu import util
from zazu import github_helper
from zazu import config
from pick import pick

def description_to_branch(description):
    """Sanitizes a string for inclusion into branch name"""
    return description.replace(' ', '_')

class IssueDescriptor:
    """Info holder of type, ticket ID, and description"""

    def __init__(self, type, id, description=''):
        self.type = type
        self.id = id
        self.description = description

    def get_branch_name(self):
        sanitized_description = self.description.replace(' ', '_')
        return '{}/{}_{}'.format(self.type, self.id, sanitized_description)


def make_ticket(issue_tracker):
    """Creates a new ticket interactively"""
    project = issue_tracker.default_project()
    project = issue_tracker.default_project()
    issue_type, idx = pick(issue_tracker.issue_types(), 'Pick issue type')
    click.echo("Making a new {} in the {} project...".format(issue_type.lower(), project))
    summary = util.prompt('Enter a title')
    description = util.prompt('Enter a description')
    component = issue_tracker.default_component()
    issue = issue_tracker.create_issue(project, issue_type, summary, description, component)
    # Self assign the new ticket
    issue_tracker.assign_issue(issue, issue.fields.reporter.name)
    return issue


def verify_ticket_exists(issue_tracker, ticket_id):
    """Verify that a given ticket exists"""
    try:
        issue = issue_tracker.issue(ticket_id)
        click.echo("Found ticket {}: {}".format(ticket_id, issue.fields.summary))
    except config.IssueTrackerError:
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
    type = None
    description = None
    if '-' not in name:
        raise click.ClickException("Branch name must be in the form PROJECT-NUMBER, type/PROJECT-NUMBER, or type/PROJECT_NUMBER_description")
    components = name.split('/')
    if len(components) == 2:
        type = components[0]
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

@dev.command()
@click.argument('name', required=False)
@click.option('--no-verify', is_flag=True, help='Skip verification that ticket exists')
@click.option('-t', '--type', type=click.Choice(['feature', 'release', 'hotfix']), help='the ticket type to make',
              default='feature')
@click.pass_context
def start(ctx, name, no_verify, type):
    """Start a new feature, much like git-flow but with more sugar"""
    if name is None:
        try:
            name = str(make_ticket(ctx.obj.issue_tracker()))
        except config.IssueTrackerError as e:
            raise click.ClickException(str(e))
        click.echo('Created ticket "{}"'.format(name))
    issue = make_issue_descriptor(name)
    if not no_verify:
        verify_ticket_exists(ctx.obj.issue_tracker(), issue.id)
    if issue.description is None:
        issue.description = util.prompt('Enter a short description for the branch')
    issue.type = type
    branch_name = issue.get_branch_name()
    offer_to_stash_changes(ctx.obj.repo)
    try:
        # Check if the target branch already exists
        ctx.obj.repo.git.checkout(branch_name)
        click.echo('Branch {} already exists!'.format(branch_name))
    except git.exc.GitCommandError:
        click.echo('Checking out develop...')
        ctx.obj.repo.heads.develop.checkout()
        click.echo('Pulling from origin...')
        try:
            ctx.obj.repo.remotes.origin.pull()
        except git.exc.GitCommandError:
            click.secho('WARNING: unable to pull from origin!', fg='red')
        click.echo('Creating new branch named "{}"...'.format(branch_name))
        ctx.obj.repo.git.checkout('HEAD', b=branch_name)


@dev.command()
@click.pass_context
def status(ctx):
    """Get status of this branch"""
    descriptor = make_issue_descriptor(ctx.obj.repo.active_branch.name)
    issue_id = descriptor.id
    if not issue_id:
        click.echo('The current branch does not contain a ticket ID')
        exit(-1)
    else:
        gh = github_helper.make_gh()

        def get_pulls_for_branch(branch):
            org, repo = github_helper.parse_github_url(ctx.obj.repo.remotes.origin.url)
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
                click.echo(click.style('    {} ({}): '.format(type, issue.fields.status.name), fg='green') + issue.fields.summary)
                click.echo(click.style('    Description: '.format(type), fg='green') + issue.fields.description.replace(config.JIRA_CREATED_BY_ZAZU, ''))
            except jira.exceptions.JIRAError:
                click.echo("    No ticket found")

            matches = pulls_future.result()
            click.secho('Pull request info:', bg='white', fg='black')
            click.echo('    {} matching PRs'.format(len(matches)))
            if matches:
                for p in matches:
                    click.echo(click.style('    PR Name:  ', fg='green') + p.title)
                    click.echo(click.style('    PR State: ', fg='green') + p.state)
                    body = '\n'.join(['\n'.join(textwrap.wrap(line, 90, break_long_words=False, initial_indent='    ',
                                                              subsequent_indent='    ')) for line in p.body.splitlines()])
                    click.echo(click.style('    PR Body:  \n', fg='green') + body)

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
        # TODO: add link to jira ticket in the PR, zazu logo
        # <img src="http://vignette1.wikia.nocookie.net/disney/images/c/ca/Zazu01cf.png" alt="Zazu" width=50"/>
    else:
        raise click.UsageError("Can't open a PR for a non-github repo")


@dev.command()
@click.pass_context
def ticket(ctx):
    """Open the JIRA ticket for this feature"""
    descriptor = make_issue_descriptor(ctx.obj.repo.active_branch.name)
    issue_id = descriptor.id
    if not issue_id:
        click.echo('The current branch does not contain a ticket ID')
        exit(-1)
    else:
        url = ctx.obj.issue_tracker().browse_url(issue_id)
        click.echo('Opening "{}"'.format(url))
        webbrowser.open_new(url)


@dev.command()
@click.pass_context
def builds(ctx):
    """Display build statuses"""
    raise NotImplementedError

