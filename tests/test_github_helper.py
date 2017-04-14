# -*- coding: utf-8 -*-

import zazu.github_helper

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_parse_github_url():
    owner = 'stopthatcow'
    name = 'zazu'
    url = 'ssh://git@github.com/{}/{}'.format(owner, name)
    owner_out, name_out = zazu.github_helper.parse_github_url(url)
    assert owner_out == owner
    assert name_out == name
