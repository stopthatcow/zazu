# -*- coding: utf-8 -*-
"""Holds the zazu repo subcommand."""
import zazu.config
import zazu.git_helper
import zazu.github_helper
import zazu.util
zazu.util.lazy_import(locals(), [
    'click',
    'functools',
    'git',
    'os',
    'semantic_version',
    'socket'
])

__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2016'


@click.group()
@zazu.config.pass_config
def repo(config):
    """Manage repository."""
    pass


@repo.command()
@zazu.config.pass_config
def init(config):
    """Install git hooks to repo."""
    config.check_repo()
    zazu.git_helper.install_git_hooks(config.repo_root)


@repo.command()
@click.argument('repository')
@click.argument('destination', required=False)
@click.option('--nohooks', is_flag=True, help='does not install git hooks in the cloned repo')
@click.option('--nosubmodules', is_flag=True, help='does not update submodules')
@zazu.config.pass_config
def clone(config, repository, destination, nohooks, nosubmodules):
    """Clone and initialize a repo.

    Args:
        repository (str): name or url of the repository to clone.
        destination (str): path to clone the repo to.
        nohooks (bool): if True, git hooks are not installed.
        nosubmodules (bool): if True submodules are not initialized.

    """
    if os.path.isdir(repository) or ':' in repository:
        repository_url = repository
    elif config.scm_hosts():
        scm_repo = config.scm_host_repo(repository)
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
@zazu.config.pass_config
def cleanup(config, remote, target_branch, yes):
    """Clean up merged/closed branches."""
    config.check_repo()
    repo_obj = config.repo
    develop_branch_name = config.develop_branch_name()
    try:
        repo_obj.heads[develop_branch_name].checkout()
    except IndexError:
        raise click.ClickException('unable to checkout "{}"'.format(develop_branch_name))
    try:
        issue_tracker = config.issue_tracker()
    except click.ClickException:
        issue_tracker = None
    closed_branches = set()
    protected_branches = config.protected_branches()
    if remote:
        repo_obj.git.fetch('--prune')
        remote_branch_names = {b.name.replace('origin/', '') for b in repo_obj.remotes.origin.refs} - protected_branches
        if issue_tracker is not None:
            closed_branches = get_closed_branches(issue_tracker, remote_branch_names)
        merged_remote_branches = zazu.git_helper.merged_branches(repo_obj, target_branch, remote=True)
        merged_remote_branches = {b.replace('origin/', '') for b in merged_remote_branches}
        empty_branches = {b for b in remote_branch_names if branch_is_empty(repo_obj,
                                                                            'origin/{}'.format(b),
                                                                            'origin/{}'.format(develop_branch_name))}
        branches_to_delete = (merged_remote_branches | closed_branches | empty_branches) - protected_branches
        if branches_to_delete:
            confirmation = 'These remote branches will be deleted: {} Proceed?'.format(zazu.util.pprint_list(branches_to_delete))
            if yes or click.confirm(confirmation):
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
            repo_obj.git.branch('-D', *branches_to_delete)


def tag_to_version(tag):
    """Convert a git tag into a semantic version string.

    i.e. R4.1 becomes 4.1.0. A leading 'r' or 'v' is optional on the tag.

    """
    components = []
    if tag is not None:
        if tag.lower().startswith('r') or tag.lower().startswith('v'):
            tag = tag[1:]
        components = tag.split('.')
    major = '0'
    minor = '0'
    patch = '0'
    try:
        major = components[0]
        minor = components[1]
        patch = components[2]
    except IndexError:
        pass

    return '.'.join([major, minor, patch])


def make_semver(repo_root, prerelease=None):
    """Parse SCM info and creates a semantic version."""
    branch_name, sha, tags = parse_describe(repo_root)
    if tags:
        # There are git tags to consider. Parse them all then choose the one that is latest (sorted by semver rules).
        return sorted([make_version_number(branch_name, prerelease, tag, sha) for tag in tags])[-1]

    return make_version_number(branch_name, prerelease, None, sha)


def parse_describe(repo_root):
    """Parse the results of git describe into branch name, sha, and tags."""
    repo = git.Repo(repo_root)
    try:
        sha = 'g{}{}'.format(repo.git.rev_parse('HEAD')[:7], '-dirty' if repo.git.status(['--porcelain']) else '')
        branch_name = repo.git.rev_parse(['--abbrev-ref', 'HEAD']).strip()
        # Get the list of tags that point to HEAD
        tag_result = repo.git.tag(['--points-at', 'HEAD'])
        tags = filter(None, tag_result.strip().split('\n'))
    except git.GitCommandError as e:
        raise click.ClickException(str(e))

    return branch_name, sha, tags


def sanitize_branch_name(branch_name):
    """Replace punctuation that cannot be in semantic version from a branch name with dashes."""
    return branch_name.replace('/', '-').replace('_', '-')


def make_version_number(branch_name, prerelease, tag, sha):
    """Convert repo metadata and build version into a semantic version."""
    branch_name_sanitized = sanitize_branch_name(branch_name)
    build_info = ['sha', sha, 'branch', branch_name_sanitized]
    prerelease_list = [str(prerelease)] if prerelease is not None else ['0']
    if tag is not None:
        version = tag_to_version(tag)
        if prerelease is not None:
            raise click.ClickException('Pre-release specifier is not allowed on tagged commits')
        prerelease_list = []
    elif branch_name.startswith('release/') or branch_name.startswith('hotfix/'):
        version = tag_to_version(branch_name.split('/', 1)[1])
    else:
        version = '0.0.0'
    semver = semantic_version.Version(version)
    semver.prerelease = prerelease_list
    semver.build = build_info

    return semver


def pep440_from_semver(semver):
    """Convert semantic version to PEP440 compliant version."""
    segment = ''
    if semver.prerelease:
        segment = '.dev{}'.format('.'.join(semver.prerelease))
    local_version = '.'.join(semver.build)
    local_version = local_version.replace('-', '.')
    version_str = '{}.{}.{}{}'.format(semver.major, semver.minor, semver.patch, segment)
    # Include the local version if we are not a true release
    if local_version and semver.prerelease:
        version_str = '{}+{}'.format(version_str, local_version)
    return version_str


@repo.command()
@click.option('--pep440', is_flag=True, help='Format the output as PEP 440 compliant')
@click.option('--prerelease', type=int, help='Pre-release number (invalid for tagged commits)')
@zazu.config.pass_config
def describe(config, pep440, prerelease):
    """Get version string describing current commit."""
    config.check_repo()
    version = make_semver(config.repo_root, prerelease)
    if pep440:
        version = pep440_from_semver(version)
    click.echo(str(version))


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
    """Return True if branch has no commits newer than base_branch."""
    try:
        return int(repo.git.rev_list('--count', branch, '^{}'.format(base_branch))) == 0
    except git.GitCommandError:
        return False
