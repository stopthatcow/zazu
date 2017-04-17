# -*- coding: utf-8 -*-

import zazu.plugins.teamcity_build_server

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_teamcity_build_server():
    zazu.plugins.teamcity_build_server.TeamCityBuildServer('teamcity')
