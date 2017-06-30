# -*- coding: utf-8 -*-
import click
import future.utils
import pytest
import re
import os
import zazu.build
import subprocess
import zazu.cmake_helper

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def test_parse_key_value_pairs():
    expected = {'foo': '1',
                'bar': '2'}
    args = ['{}={}'.format(k, v) for k, v in future.utils.iteritems(expected)]
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


def test_make_semver_tagged(git_repo):
    ver_re = re.compile('1\.2\.3\+sha\..*\.build\.4\.branch\.master')
    git_repo.git.tag('-a', '1.2.3', '-m', 'my message')
    version = zazu.build.make_semver(git_repo.working_tree_dir, 4)
    assert ver_re.match(str(version))
    # Tag again, to ensure we sort by semver
    git_repo.git.tag('-a', '1.2.4', '-m', 'my message')
    version = zazu.build.make_semver(git_repo.working_tree_dir, 5)
    assert str(version).startswith('1.2.4+')


def test_make_semver_empty_repo(empty_repo):
    with pytest.raises(click.ClickException):
        zazu.build.make_semver(empty_repo.working_tree_dir, 0)


def test_build(repo_with_build_config, mocker):
    mocker.patch('subprocess.call', return_value=0)
    dir = repo_with_build_config.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['build', '--arch=host', '--verbose', 'echo_foobar'])
        assert not result.exit_code
        assert subprocess.call.call_args[0][0] == 'echo "foobar"'
        # This call is an error due to the ambiguous architecture.
        result = runner.invoke(zazu.cli.cli, ['build', '--verbose', 'echo_foobar'])
        assert result.exit_code
        assert 'No arch specified, but there are multiple arches available' in result.output


def test_build_bad_exit(repo_with_build_config, mocker):
    mocker.patch('subprocess.call', return_value=1)
    dir = repo_with_build_config.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['build', '--arch=host', 'echo_foobar'])
        assert result.exit_code == 1
        assert 'Error: echo "foobar" exited with code 1' in result.output


def test_cmake_build(repo_with_build_config, mocker):
    mocker.patch('zazu.cmake_helper.configure', return_value=0)
    mocker.patch('zazu.cmake_helper.build', return_value=0)
    dir = repo_with_build_config.working_tree_dir
    with zazu.util.cd(dir):
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
        assert not result.exit_code


def test_cmake_configure_error(repo_with_build_config, mocker):
    mocker.patch('zazu.cmake_helper.configure', return_value=1)
    dir = repo_with_build_config.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['build', 'cmake_build'])
        assert result.exit_code
        zazu.cmake_helper.configure.assert_called_once()
        assert result.output.endswith('Error configuring with cmake\n')


def test_cmake_build_error(repo_with_build_config, mocker):
    mocker.patch('zazu.cmake_helper.configure', return_value=0)
    mocker.patch('zazu.cmake_helper.build', return_value=1)
    dir = repo_with_build_config.working_tree_dir
    with zazu.util.cd(dir):
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
    semver = zazu.build.make_version_number('master', 1, '1.1', 'abcdef1')
    assert str(semver) == '1.1.0+sha.abcdef1.build.1.branch.master'
    semver = zazu.build.make_version_number('release/1.2', 1, None, 'abcdef1')
    assert str(semver) == '1.2.0-1+sha.abcdef1.build.1.branch.release-1.2'
    semver = zazu.build.make_version_number('hotfix/1.2.1', 1, None, 'abcdef1')
    assert str(semver) == '1.2.1-1+sha.abcdef1.build.1.branch.hotfix-1.2.1'
    semver = zazu.build.make_version_number('feature/name', 1, None, 'abcdef1')
    assert str(semver) == '0.0.0-1+sha.abcdef1.build.1.branch.feature-name'


def test_component_configuration(repo_with_build_config):
    dir = repo_with_build_config.working_tree_dir
    project_config = zazu.config.Config(dir).project_config()
    component = zazu.build.ComponentConfiguration(project_config['components'][0])
    component.description() == 'The description'
    component.name() == 'zazu'
    goals = component.goals()
    assert len(goals) == 2
    echo_foobar_spec = component.get_spec('echo_foobar', 'host'
                                                         '', 'release')
    assert echo_foobar_spec.build_description() == 'echo_foobar build description'
    assert echo_foobar_spec.build_type() == 'release'
    assert echo_foobar_spec.build_artifacts() == ['artifact.zip']
    echo_foobar_goal = goals['echo_foobar']
    assert echo_foobar_goal.name() == 'echo_foobar'
    assert echo_foobar_goal.goal() == 'echo_foobar'
    assert echo_foobar_goal.description() == 'echo_foobar description'
    echo_foobar_builds = echo_foobar_goal.builds()
    assert len(echo_foobar_builds) == 2
    assert 'host' in echo_foobar_builds
    fake_spec = component.get_spec('fake', None, 'release')
    assert fake_spec.build_goal() == 'fake'
