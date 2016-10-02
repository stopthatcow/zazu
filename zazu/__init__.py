import pkg_resources

name = 'zazu'
version_file_path = pkg_resources.resource_filename('zazu', 'version.txt')

with open(version_file_path, 'r') as version_file:
    __version__ = version_file.readline().rstrip()
