import click
import zazu.teamcity_helper
import zazu.git_helper
import zazu.build

@click.group()
@click.pass_context
def repo(ctx):
    """Manage repository"""
    ctx.obj.check_repo()


@repo.group()
def setup():
    """Setup repository with services"""
    pass


@setup.command()
@click.pass_context
def hooks(ctx):
    """Setup default git hooks"""
    zazu.git_helper.install_git_hooks(ctx.obj.repo_root)


@setup.command()
@click.pass_context
def ci(ctx):
    """Setup TeamCity configurations based on a zazu.yaml file"""
    address = 'teamcity.lily.technology'
    port = 8111
    ctx.obj.check_repo()
    ctx.obj._tc = zazu.teamcity_helper.make_tc(address, port)
    try:
        project_config = ctx.obj.project_config()
        if click.confirm("Post build configuration to TeamCity?"):
            components = project_config['components']
            for c in components:
                component = zazu.build.ComponentConfiguration(c)
                zazu.teamcity_helper.setup(ctx.obj._tc, component, ctx.obj.repo_root)
    except IOError:
        raise click.ClickException("No {} file found in {}".format(project_file_name, ctx.obj.repo_root))


@repo.command()
@click.pass_context
def clone(ctx):
    """Clone and initialize a repo"""
    raise NotImplementedError


@repo.command()
@click.pass_context
def init(ctx):
    """Initialize repo directory structure"""
    raise NotImplementedError


@repo.command()
@click.option('-r', '--remote', is_flag=True, help='Also clean up remote branches')
@click.option('-b', '--target_branch', default='origin/master', help='Delete branches merged with this branch')
@click.pass_context
def cleanup(ctx, remote, target_branch):
    """Clean up merged branches"""
    def filter_undeletable(branches):
        """Filters out branches that we don't want to delete"""
        return filter(lambda s: not ('master' == s or 'develop' == s or '*' in s or '-' == s), branches)

    ctx.obj.repo.git.checkout('develop')
    if remote:
        ctx.obj.repo.git.fetch('--prune')
        merged_remote_branches = filter_undeletable(zazu.git_helper.get_merged_branches(ctx.obj.repo, 'origin/master', remote=True))
        if merged_remote_branches:
            click.echo('The following remote branches will be deleted:')
            for b in merged_remote_branches:
                click.echo('    - {}'.format(b))
            if click.confirm('Proceed?'):
                for b in merged_remote_branches:
                    click.echo('Deleting {}'.format(b))
                    ctx.obj.repo.git.push('--delete', 'origin', b.replace('origin/', ''))
    merged_branches = filter_undeletable(zazu.git_helper.get_merged_branches(ctx.obj.repo, target_branch))
    if merged_branches:
        click.echo('The following local branches will be deleted:')
        for b in merged_branches:
            click.echo('    - {}'.format(b))
        if click.confirm('Proceed?'):
            for b in merged_branches:
                click.echo('Deleting {}'.format(b))
                ctx.obj.repo.git.branch('-d', b)
