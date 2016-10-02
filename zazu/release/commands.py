

import click
import functools
import git
import os
import re
import semantic_version


base_url = 'git@github.com:LilyRobotics/'

RELEASE_STARTING_BRANCH='develop'

@click.group()
@click.pass_context
def release(ctx):
    """Manage releases"""
    ctx.obj.check_repo()


def update_to_branch(g, branch):
    """Updates a repo and its submodules to the tip of a given branch"""
    g.git.checkout('-f', branch)
    g.git.pull()
    g.git.submodule('update', '-f', '--init', '--recursive')


def pull_repo(r, branch):
    if not os.path.isdir(r):
        git.Git().clone('--recurse-submodules', "{}{}.git".format(base_url, r), r)
    g = git.Repo(r)
    update_to_branch(g, branch)
    return g


def repo_belongs_to_lily(repo):
    return 'LilyRobotics' in repo.remotes.origin.url


def branch_repo(g, name, base):
    """updates to 'name' branch if it exists, otherwise makes a branch starting on the 'base' branch"""
    try:
        g.git.checkout('-f', name)
        g.git.pull()
    except git.exc.GitCommandError:
        g.git.checkout('-f', base)
        g.git.pull()
        g.git.checkout('-b', name)
        g.git.push('-u')


def submodule_branch(g, branch_name, base_branch=RELEASE_STARTING_BRANCH):
    """recursively update submodules to a specific branch"""
    submodule_do(g, pre_action=functools.partial(branch_repo, name=branch_name, base=base_branch))


def submodule_release(g, release_name):
    """recursively release submodules to develop and master"""
    submodule_do(g, post_action=functools.partial(release_repo, starting_branch='release/{}'.format(release_name), tag=release_name))

def submodule_walk(g, action=lambda x:x, filter=repo_belongs_to_lily):
    """recursively walk submodules from the bottom up"""
    modules_to_be_updated = [m for m in g.submodules if filter(m.module())]
    if modules_to_be_updated:
        for s in modules_to_be_updated:
            submodule_walk(s.module(), action)
    action(g)

def submodule_do(g, pre_action=lambda x:x, post_action=lambda x:x, filter=repo_belongs_to_lily):
    """recursively perform an action on a repo and its submodules from the bottom up, and commit if there are changes"""
    modules_to_be_updated = [m for m in g.submodules if filter(m.module())]
    if modules_to_be_updated:
        for s in modules_to_be_updated:
            submodule_do(s.module(), pre_action, post_action)
    pre_action(g)
    modules_modified = [m for m in modules_to_be_updated if g.git.diff(m.name)]
    if modules_modified:
        g.git.add(modules_modified)
        g.git.commit('-m', 'submodule update')
        g.git.push()
    post_action(g)

def validate_release_name(version):
    """Validates that a version is a valid semantic version"""
    try:
        semantic_version.Version(version)
    except ValueError:
        raise click.ClickException('"{}" is not a valid semantic version'.format(version))


@release.command()
@click.argument('version')
@click.pass_context
def start(ctx, version):
    """Create a branch named "release/version" including submodules starting from RELEASE_STARTING_BRANCH"""
    validate_release_name(version)
    click.echo('Starting release "{}"'.format(version))
    branch_name = 'release/{}'.format(version)
    update_to_branch(ctx.obj.repo, RELEASE_STARTING_BRANCH)
    submodule_branch(ctx.obj.repo, branch_name, RELEASE_STARTING_BRANCH)
    click.echo('Release branch "{}" is ready'.format(branch_name))


def release_repo(g, starting_branch, tag):
    """Merges 'starting_branch' to master and tags master with 'tag'"""
    update_to_branch(g, 'master')
    click.echo('Merging to master')
    g.git.merge(starting_branch)
    click.echo('Tagging master as {}'.format(tag))
    g.git.tag(tag)
    g.git.push()


@release.command()
@click.argument('version')
@click.pass_context
def finish(ctx, release_name):
    """merge release branch to master, tag master branch, merge release branch to develop"""
    validate_release_name(version)
    release_branch_name = 'release/{}'.format(release_name)
    click.echo('Releasing {}'.format(r))
    submodule_branch(ctx.obj.repo, release_branch_name)
    submodule_release(ctx.obj.repo, release_name)
    # Now update the develop branch with all the new develop heads
    submodule_branch(ctx.obj.repo, 'develop', release_branch_name)


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
    """Check all of the submodules abe be sure that any shared ones are on the same version"""
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
    for k,v in modules.items():
        if len(set(v))>1:
            raise click.ClickException('Version mismatch in "{}": {}'.format(k, v))
