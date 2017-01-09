# -*- coding: utf-8 -*-
import click
import pytest
import zazu.build

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_parse_key_value_pairs():
    expected = {'foo': '1',
                'bar': '2'}
    args = ['{}={}'.format(k, v) for k, v in expected.iteritems()]
    print(args)
    parsed = zazu.build.parse_key_value_pairs(args)
    assert expected == parsed
    assert not zazu.build.parse_key_value_pairs('')


def test_bad_parse_key_value_pairs():
    with pytest.raises(click.ClickException):
        zazu.build.parse_key_value_pairs('foo')


def test_tag_to_version():
    valid_versions = ['r1.2.3', '1.2.3', '1.2.3']
    for ver in valid_versions:
        assert '1.2.3' == zazu.build.tag_to_version(ver)
    assert '1.2.0' == zazu.build.tag_to_version('1.2')
    assert '1.0.0' == zazu.build.tag_to_version('1')
