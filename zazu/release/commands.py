

import click
import functools
import re
import zazu

RELEASE_STARTING_BRANCH = 'develop'
RELEASE_TARGET_BRANCH = 'master'


@click.group()
@click.pass_context
def release(ctx):
    """Manage releases"""
    ctx.obj.check_repo()


def update_to_branch(g, branch, dry_run):
    """Updates a repo and its submodules to the tip of a given branch"""
    zazu.info('[{}] Checkout "{}"'.format(g.working_tree_dir, branch))
    zazu.info('[{}] Pull "{}"'.format(g.working_tree_dir, branch))
    zazu.info('[{}] Submodule update'.format(g.working_tree_dir))
    if not dry_run:
        g.git.checkout('-f', branch)
        g.git.pull()
        g.git.submodule('update', '-f', '--init', '--recursive')


def merge_branch(g, branch, dry_run):
    """Merges a branch into a target branch and updates submodules"""
    zazu.info('[{}] Merge "{}"'.format(g.working_tree_dir, branch))
    zazu.info('[{}] Submodule update'.format(g.working_tree_dir))
    if not dry_run:
        g.git.merge(branch)
        g.git.submodule('update', '-f', '--init', '--recursive')


def repo_belongs_to_lily(repo):
    return 'LilyRobotics' in repo.remotes.origin.url


def branch_repo(g, name, base, dry_run):
    """updates to 'name' branch if it exists, otherwise makes a branch starting on the 'base' branch"""
    zazu.info('[{}] Checkout branch "{}" based on "{}"'.format(g.working_tree_dir, name, base))
    if not dry_run:
        import git
        try:
            g.git.checkout('-f', name)
            g.git.pull()
            g.git.submodule('update', '-f', '--init', '--recursive')
        except git.exc.GitCommandError:
            g.git.checkout('-f', base)
            g.git.pull()
            g.git.submodule('update', '-f', '--init', '--recursive')
            g.git.checkout('-b', name)
            g.git.push('-u')


def submodule_branch(g, branch_name, base_branch=RELEASE_STARTING_BRANCH, dry_run=False):
    """recursively update submodules to a specific branch"""
    setup_action = functools.partial(branch_repo, name=branch_name, base=base_branch, dry_run=dry_run)
    submodule_do(g, setup_action=setup_action, dry_run=dry_run)


def submodule_release(g, release_name, dry_run=False):
    """recursively release repo to master"""
    setup_action = functools.partial(update_to_branch, branch=RELEASE_TARGET_BRANCH, dry_run=dry_run)
    post_action = functools.partial(release_repo, starting_branch='release/{}'.format(release_name), tag=release_name, dry_run=dry_run)
    submodule_do(g, setup_action=setup_action, post_action=post_action, dry_run=dry_run)


def submodule_walk(g, action=lambda x: x, filter=repo_belongs_to_lily):
    """recursively walk submodules from the bottom up"""
    modules_to_be_updated = [m for m in g.submodules if filter(m.module())]
    if modules_to_be_updated:
        for s in modules_to_be_updated:
            submodule_walk(s.module(), action)
    action(g)


def submodule_do(g, setup_action=lambda x: x, pre_action=lambda x: x, post_action=lambda x: x, filter=repo_belongs_to_lily, dry_run=False):
    """recursively perform an action on a repo and its submodules from the bottom up, and commit if there are changes"""
    setup_action(g)
    modules_to_be_updated = [m for m in g.submodules if filter(m.module())]
    if modules_to_be_updated:
        for s in modules_to_be_updated:
            submodule_do(s.module(), setup_action, pre_action, post_action, filter=filter, dry_run=dry_run)
    pre_action(g)
    if modules_to_be_updated:
        if not dry_run:
            modules_modified = [m for m in modules_to_be_updated if g.git.diff(m.name)]
            if modules_modified:
                zazu.echo("[{}] Commit submodules".format(g.working_tree_dir))
                g.git.add(modules_modified)
                g.git.commit('-m', 'submodule update')
                zazu.info("[{}] push".format(g.working_tree_dir))
                g.git.push()
        else:
            zazu.info("[{}] Would commit submodules".format(g.working_tree_dir.path))
    post_action(g)


def validate_release_name(version):
    """Validates that a version is a valid semantic version"""
    import semantic_version
    try:
        semantic_version.Version(version)
    except ValueError:
        raise click.ClickException('"{}" is not a valid semantic version'.format(version))


@release.command()
@click.option('--dry-run', is_flag=True)
@click.argument('version')
@click.pass_context
def start(ctx, version, dry_run):
    """Create a branch named "release/version" including submodules starting from RELEASE_STARTING_BRANCH"""
    validate_release_name(version)
    zazu.info('Starting release "{}"'.format(version))
    branch_name = 'release/{}'.format(version)
    update_to_branch(ctx.obj.repo, RELEASE_STARTING_BRANCH, dry_run)
    submodule_branch(ctx.obj.repo, branch_name, RELEASE_STARTING_BRANCH, dry_run)
    zazu.info('Release branch "{}" is ready'.format(branch_name))


def release_repo(g, starting_branch, tag, dry_run):
    """Merges 'starting_branch' to RELEASE_TARGET_BRANCH and tags RELEASE_TARGET_BRANCH with 'tag'"""
    merge_branch(g, starting_branch, dry_run)
    if not dry_run:
        g.git.tag(tag, '-fam', 'tagged by zazu')
        g.git.push('--follow-tags', '-f')
    zazu.info('[{}] Tag {} as {}'.format(g.working_tree_dir, RELEASE_TARGET_BRANCH, tag))


@release.command()
@click.option('--dry-run', is_flag=True)
@click.argument('version')
@click.pass_context
def finish(ctx, version, dry_run):
    """merge release branch to RELEASE_TARGET_BRANCH, tag RELEASE_TARGET_BRANCH branch, merge release branch to develop"""
    validate_release_name(version)
    release_branch_name = 'release/{}'.format(version)
    zazu.info('Updating to latest on "{}"'.format(release_branch_name))
    submodule_branch(ctx.obj.repo, release_branch_name, dry_run=dry_run)
    zazu.info('Releasing {}'.format(version))
    submodule_release(ctx.obj.repo, version, dry_run=dry_run)
    # TODO update the develop branch with all the new develop heads


class GitUrl:
    """Parses a git url and allows extraction of base url and repo name"""

    def __init__(self, url):
        regex = '((git|http|https|ssh)(://))?((\w+)(@))?([\w\.\\-~]+)((:\d+/)|(:|/))([\w\./\:\-~]+)(\.git)(/)?'
        self.match = re.match(regex, url.lower())
        if not self.match:
            raise Exception('unable to parse repo info from url {}'.format(url))

    def name(self):
        return self.match.group(11)

    def base_url(self):
        return self.match.group(7)

    def __hash__(self):
        return hash(self.base_url() + self.name())

    def __eq__(self, other):
        return other.name() == self.name() and other.base_url() == self.base_url()


def collect_submodules(g, modules):
    modules.append(g)


@release.command()
@click.pass_context
def status(ctx):
    """Check all of the submodules and be sure that any shared ones are on the same version"""
    map = []
    submodule_walk(ctx.obj.repo, functools.partial(collect_submodules, modules=map))
    modules = {}
    for g in map:
        name = GitUrl(g.remotes.origin.url).name()
        describe = g.git.describe()
        if name in modules:
            modules[name].append(describe)
        else:
            modules[name] = [describe]
    for k, v in modules.items():
        if len(set(v)) > 1:
            raise click.ClickException('Version mismatch in "{}": {}'.format(k, v))


@release.command()
@click.option('--dry-run', is_flag=True)
@click.option('-b', '--branch', default='develop', help='The branch name to update to')
@click.pass_context
def update(ctx, branch, dry_run):
    submodule_branch(ctx.obj.repo, branch, ctx.obj.repo.active_branch.name, dry_run=dry_run)
