import pkg_resources

name = 'zazu'
version_file_path = pkg_resources.resource_filename('zazu', 'version.txt')
try:
    with open(version_file_path, 'r') as version_file:
        __version__ = version_file.readline().rstrip()
except IOError:
    __version__ = "unknown"

verbose_level = 0


def echo(message, level=0):
    """Print to terminal"""
    if level <= verbose_level:
        print(message)


def info(message):
    """Echo out at level 1"""
    echo(message, level=1)


def debug(message):
    """Echo out at level 2"""
    echo(message, level=2)
