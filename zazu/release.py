
import git
import os
import concurrent.futures
import multiprocessing
import functools
import re

base_url = 'git@github.com:LilyRobotics/'
repos = [
    'build',
    'network_interface',
    'stm32_bootloader',
    'PX4',
    'tracker'
]


def update_to_branch(g, branch):
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
    g.git.checkout('-f', base)
    g.git.pull()
    try:
        g.git.checkout('-f', name)
        g.git.pull()
    except git.exc.GitCommandError:
        g.git.checkout('-b', name)
        g.git.push('-u')


def submodule_branch(g, branch_name, base_branch='develop'):
    """recursively update submodules to a specific branch"""
    submodule_do(g, functools.partial(branch_repo, name=branch_name, base=base_branch))


def submodule_release(g, release_name):
    """recursively update submodules to a specific branch"""
    submodule_do(g, functools.partial(release_repo, starting_branch='release/{}'.format(release_name), tag=release_name))


def submodule_do(g, action, filter=repo_belongs_to_lily):
    """recursively perform an action on a repo and its submodules from the bottom up, and commit if there are changes"""
    modules_to_be_updated = [m for m in g.submodules if filter(m.module())]
    if modules_to_be_updated:
        for s in modules_to_be_updated:
            submodule_do(s.module(), action)
    action(g)
    modules_modified = [m for m in modules_to_be_updated if g.git.diff(m.name)]
    if modules_modified:
        g.git.add(modules_modified)
        g.git.commit('-m', 'submodule update')
        g.git.push()


def start_repo(repo, release):
    print('Starting release {} on {}'.format(release, repo))
    g = pull_repo(repo, 'develop')
    branch_name = 'release/{}'.format(release)
    submodule_branch(g, branch_name, 'develop')
    return 'Release branch {} is ready in {}'.format(branch_name, repo)


def start(release):
    with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = {executor.submit(start_repo, r, release): r for r in repos}
        for future in concurrent.futures.as_completed(futures):
            print(future.result())


def release_repo(g, starting_branch, tag):
    update_to_branch(r, 'develop')
    print('Merging to develop')
    g.git.merge(starting_branch)
    update_to_branch(r, 'master')
    print('Merging to master')
    g.git.merge(starting_branch)
    print('Tagging master as {}'.format(tag))
    g.git.tag(tag)
    g.git.push()


def finish(release_name):
    release_branch_name = 'release/{}'.format(release_name)
    for r in repos:
        print('Releasing {}'.format(r))
        g = pull_repo(r, release_branch_name)
        submodule_branch(g, release_branch_name)
        submodule_release(g, release_name)


class GitUrl:

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


def describe_repo(g):
    info = GitUrl(g.remotes.origin.url)
    print '    {} {} {}'.format(g.git.describe(), info.name(), info.base_url())


def describe():
    for r in repos:
        print('Describing {}'.format(r))
        g = git.Repo(r)
        submodule_do(g, describe_repo)

describe()
start('R16')


# Release start
# create or update all submodules branches from a base branch
# Release finish
# merge release to develop
# merge release branch to master
# tag master branch
# Release status
# check status of a release by showing release PR status
# show ticket status of things tagged in the release
# show builds associated with the release branch
# show all SHAs of all modules, and show error if they do not match
