# -*- coding: utf-8 -*-
import click
import tests.conftest
import distutils.spawn
import pytest
import zazu.cli
import zazu.style


def write_c_file_with_bad_style(file):
    with open(file, 'w') as f:
        f.write('void main(){\n\n}\n ')


def write_py_file_with_bad_style(file):
    with open(file, 'w') as f:
        f.write('def main():\tpass\n\n\n ')


@pytest.fixture()
def repo_with_style_errors(repo_with_style):
    dir = repo_with_style.working_tree_dir
    with tests.conftest.working_directory(dir):
        write_c_file_with_bad_style('temp.c')
        write_c_file_with_bad_style('temp.cc')
        write_c_file_with_bad_style('temp.cpp')
        write_c_file_with_bad_style('temp.hpp')
        write_c_file_with_bad_style('temp.h')
        write_py_file_with_bad_style('temp.py')
    return repo_with_style


@pytest.mark.skipif(not distutils.spawn.find_executable('astyle'),
                    reason="requires astyle")
def test_astyle(git_repo):
    dir = git_repo.working_tree_dir
    with tests.conftest.working_directory(dir):
        bad_file_name = 'temp.c'
        write_c_file_with_bad_style(bad_file_name)
        styler = zazu.plugins.astyle_styler.AstyleStyler()
        ret = styler.run([bad_file_name], verbose=False, dry_run=True, working_dir=dir)
        assert dict(ret)[bad_file_name]
        ret = styler.run([bad_file_name], verbose=False, dry_run=False, working_dir=dir)
        assert dict(ret)[bad_file_name]
        ret = styler.run([bad_file_name], verbose=False, dry_run=True, working_dir=dir)
        assert not any(dict(ret).values())


def test_autopep8(git_repo):
    dir = git_repo.working_tree_dir
    with tests.conftest.working_directory(dir):
        bad_file_name = 'temp.py'
        write_py_file_with_bad_style(bad_file_name)
        styler = zazu.plugins.autopep8_styler.Autopep8Styler()
        ret = styler.run([bad_file_name], verbose=False, dry_run=True, working_dir=dir)
        assert dict(ret)[bad_file_name]
        ret = styler.run([bad_file_name], verbose=True, dry_run=False, working_dir=dir)
        assert dict(ret)[bad_file_name]
        ret = styler.run([bad_file_name], verbose=True, dry_run=True, working_dir=dir)
        assert not any(dict(ret).values())


@pytest.mark.skipif(not distutils.spawn.find_executable('clang-format'),
                    reason="requires clang-format")
def test_clang_format(git_repo):
    dir = git_repo.working_tree_dir
    with tests.conftest.working_directory(dir):
        bad_file_name = 'temp.c'
        write_c_file_with_bad_style(bad_file_name)
        styler = zazu.plugins.clang_format_styler.ClangFormatStyler(['-style=google'])
        ret = styler.run([bad_file_name], verbose=False, dry_run=True, working_dir=dir)
        assert dict(ret)[bad_file_name]
        ret = styler.run([bad_file_name], verbose=True, dry_run=False, working_dir=dir)
        assert dict(ret)[bad_file_name]
        ret = styler.run([bad_file_name], verbose=True, dry_run=True, working_dir=dir)
        assert not dict(ret)[bad_file_name]


@pytest.mark.skipif(not distutils.spawn.find_executable('astyle'),
                    reason="requires astyle")
def test_bad_style(repo_with_style_errors):
    dir = repo_with_style_errors.working_tree_dir
    with tests.conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['style', '--check', '-v'])
        assert result.exit_code
        assert result.output.endswith('6 files with violations in 6 files\n')
        result = runner.invoke(zazu.cli.cli, ['style', '-v'])
        assert result.exit_code == 0
        assert result.output.endswith('6 files fixed in 6 files\n')
        result = runner.invoke(zazu.cli.cli, ['style', '--check'])
        assert result.exit_code == 0


@pytest.mark.skipif(not distutils.spawn.find_executable('astyle'),
                    reason="requires astyle")
def test_dirty_style(repo_with_style_errors, monkeypatch):
    dir = repo_with_style_errors.working_tree_dir
    with tests.conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['style', '--check', '--dirty', '-v'])
        assert result.exit_code == 0
        assert result.output == '0 files with violations in 0 files\n'
        monkeypatch.setattr('zazu.git_helper.get_touched_files', lambda x: ['temp.c'])
        result = runner.invoke(zazu.cli.cli, ['style', '--check', '--dirty', '-v'])
        assert result.exit_code
        assert result.output.endswith('1 files with violations in 1 files\n')


def test_style_no_config(repo_with_missing_style):
    dir = repo_with_missing_style.working_tree_dir
    with tests.conftest.working_directory(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['style'])
        assert result.output == 'no style settings found\n'
        assert result.exit_code == 0
