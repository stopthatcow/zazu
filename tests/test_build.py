# -*- coding: utf-8 -*-
import click
import future.utils
import pytest
import re
import os
import tests.conftest
import zazu.build
import subprocess
import zazu.cmake_helper

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


def test_build(repo_with_build_config, mocker):
    mocker.patch('subprocess.call', return_value=0)
    dir = repo_with_build_config.working_tree_dir
    with tests.conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['build', 'echo_foobar'])
        assert not result.exit_code
    assert subprocess.call.call_args[0][0] == 'echo "foobar"'


def test_cmake_build(repo_with_build_config, mocker):
    mocker.patch('zazu.cmake_helper.configure', return_value=0)
    mocker.patch('zazu.cmake_helper.build', return_value=0)
    dir = repo_with_build_config.working_tree_dir
    with tests.conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['build', 'cmake_build'])
        assert not result.exit_code
        zazu.cmake_helper.configure.assert_called_once()
        assert dir in zazu.cmake_helper.configure.call_args[0][0]
        assert str(os.path.join(dir, 'build')) in zazu.cmake_helper.configure.call_args[0][1]
        zazu.cmake_helper.build.assert_called_once()
        assert dir in zazu.cmake_helper.build.call_args[0][0]
        assert 'host' == zazu.cmake_helper.build.call_args[0][1]
        assert 'minSizeRel' == zazu.cmake_helper.build.call_args[0][2]
        assert 'cmake_build' == zazu.cmake_helper.build.call_args[0][3]
        # Build again, to make sure existing directories don't break things
        result = runner.invoke(zazu.cli.cli, ['build', 'cmake_build'])


def test_cmake_configure_error(repo_with_build_config, mocker):
    mocker.patch('zazu.cmake_helper.configure', return_value=1)
    dir = repo_with_build_config.working_tree_dir
    with tests.conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['build', 'cmake_build'])
        assert result.exit_code
        zazu.cmake_helper.configure.assert_called_once()
        assert result.output.endswith('Error configuring with cmake\n')


def test_cmake_build_error(repo_with_build_config, mocker):
    mocker.patch('zazu.cmake_helper.configure', return_value=0)
    mocker.patch('zazu.cmake_helper.build', return_value=1)
    dir = repo_with_build_config.working_tree_dir
    with tests.conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['build', 'cmake_build'])
        assert result.exit_code
        zazu.cmake_helper.configure.assert_called_once()
        zazu.cmake_helper.build.assert_called_once()
        assert result.output.endswith('Error building with cmake\n')


def test_cmake_build_bad_arch():
    with pytest.raises(click.BadParameter) as e:
        zazu.build.cmake_build('', 'bad_arch', 'release', all, False, {})
    assert 'Arch "bad_arch" not recognized,' in str(e)


def test_make_version_number():
    semver = zazu.build.make_version_number('master', 1, '1.1', 0, 'abcdef1')
    assert str(semver) == '1.1.0+sha.abcdef1.build.1.branch.master'
    semver = zazu.build.make_version_number('release/1.2', 1, '1.1', 1, 'abcdef1')
    assert str(semver) == '1.2.0-1+sha.abcdef1.build.1.branch.release-1.2'
    semver = zazu.build.make_version_number('hotfix/1.2.1', 1, '1.1', 1, 'abcdef1')
    assert str(semver) == '1.2.1-1+sha.abcdef1.build.1.branch.hotfix-1.2.1'
    semver = zazu.build.make_version_number('feature/name', 1, '1.1', 1, 'abcdef1')
    assert str(semver) == '0.0.0-1+sha.abcdef1.build.1.branch.feature-name'
