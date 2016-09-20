import click
import tool_helper


@click.group()
def tool():
    """Manage tools that zazu is familiar with"""
    pass


@tool.command()
@click.option('--force-reinstall', help='forces reinstallation', is_flag=True)
@click.argument('spec')
def install(spec, force_reinstall):
    """Install tools that zazu is familiar with"""
    tool_helper.install_spec(spec, force_reinstall, click.echo)


@tool.command()
@click.argument('spec')
def uninstall(spec):
    """Uninstall tools that zazu is familiar with"""
    tool_helper.uninstall_spec(spec, click.echo)
