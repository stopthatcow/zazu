# -*- coding: utf-8 -*-
import click
import conftest
import pytest
import zazu.cli
import zazu.style


def write_bad_file(file):
    with open(file, 'w') as f:
        f.write('\n ')


def test_astyle(git_repo):
    dir = git_repo.working_tree_dir
    with conftest.working_directory(dir):
        bad_file_name = 'temp.c'
        write_bad_file(bad_file_name)
        ret = zazu.style.astyle([bad_file_name], {}, check=True, working_dir=dir)
        assert bad_file_name in ret
        ret = zazu.style.astyle([bad_file_name], {}, check=False, working_dir=dir)
        assert bad_file_name in ret
        ret = zazu.style.astyle([bad_file_name], {}, check=True, working_dir=dir)
        assert not ret


def test_autopep8(git_repo):
    dir = git_repo.working_tree_dir
    with conftest.working_directory(dir):
        bad_file_name = 'temp.py'
        write_bad_file(bad_file_name)
        ret = zazu.style.autopep8([bad_file_name], {}, check=True, working_dir=dir)
        assert bad_file_name in ret
        ret = zazu.style.autopep8([bad_file_name], {}, check=False, working_dir=dir)
        assert bad_file_name in ret
        ret = zazu.style.autopep8([bad_file_name], {}, check=True, working_dir=dir)
        assert not ret


@pytest.fixture()
def repo_with_style_errors(repo_with_style):
    dir = repo_with_style.working_tree_dir
    with conftest.working_directory(dir):
        write_bad_file('temp.c')
        write_bad_file('temp.cpp')
        write_bad_file('temp.hpp')
        write_bad_file('temp.h')
        write_bad_file('temp.py')
    return repo_with_style


def test_bad_style(repo_with_style_errors):
    dir = repo_with_style_errors.working_tree_dir
    with conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['style', '--check'])
        assert result.exit_code == -1
        assert result.output.endswith('5 files with violations in 5 files\n')
        result = runner.invoke(zazu.cli.cli, ['style'])
        assert result.exit_code == 0
        assert result.output.endswith('5 files fixed in 5 files\n')
        result = runner.invoke(zazu.cli.cli, ['style', '--check'])
        assert result.exit_code == 0


def test_dirty_style(repo_with_style_errors, monkeypatch):
    dir = repo_with_style_errors.working_tree_dir
    with conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['style', '--check', '--dirty'])
        assert result.exit_code == 0
        assert result.output == '0 files with violations in 0 files\n'
        monkeypatch.setattr('zazu.git_helper.get_touched_files', lambda x: ['temp.c'])
        result = runner.invoke(zazu.cli.cli, ['style', '--check', '--dirty'])
        assert result.exit_code == -1
        assert result.output.endswith('1 files with violations in 1 files\n')


def test_style_no_config(repo_with_no_zazu_file):
    dir = repo_with_no_zazu_file.working_tree_dir
    with conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['style'])
        assert result.output == 'Error: unable to parse config file\n'
        assert result.exit_code == -1


def test_style_no_config(repo_with_missing_style):
    dir = repo_with_missing_style.working_tree_dir
    with conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['style'])
        assert result.output == 'no style settings found\n'
        assert result.exit_code == 0
