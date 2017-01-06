# -*- coding: utf-8 -*-
"""lazily loads the version info"""


class Version:

    def __str__(self):
        import pkg_resources
        version_file_path = pkg_resources.resource_filename('zazu', 'version.txt')

        try:
            with open(version_file_path, 'r') as version_file:
                ret = version_file.readline().rstrip()
        except IOError:
            ret = "unknown"
        return ret
