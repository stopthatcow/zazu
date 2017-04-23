# -*- coding: utf-8 -*-
import click
import future.utils
import pytest
import re
import zazu.build

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_parse_key_value_pairs():
    expected = {'foo': '1',
                'bar': '2'}
    args = ['{}={}'.format(k, v) for k, v in future.utils.iteritems(expected)]
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


def test_sanitize_branch_name():
    assert 'feature-ZZ-333-foobar' == zazu.build.sanitize_branch_name('feature/ZZ-333_foobar')


def test_make_semver(git_repo):
    ver_re = re.compile('0\.0\.0-4\+sha\..*\.build\.4\.branch\.master')
    version = zazu.build.make_semver(git_repo.working_tree_dir, 4)
    assert ver_re.match(str(version))
    pep440_re = re.compile('0\.0\.0.dev4\+sha\..*\.build\.4\.branch\.master')
    pep440_version = zazu.build.pep440_from_semver(version)
    assert pep440_re.match(pep440_version)
    args = {}
    zazu.build.add_version_args(git_repo.working_tree_dir, 4, args)
    assert args['ZAZU_BUILD_VERSION'] == str(version)
    assert args['ZAZU_BUILD_VERSION_PEP440'] == pep440_version

