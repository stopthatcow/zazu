# -*- coding: utf-8 -*-
import click
import distutils.spawn
import pytest
import zazu.cli
import zazu.style
import zazu.util


def write_c_file_with_bad_style(file):
    with open(file, 'w') as f:
        f.write('void main(){\n\n}\n \n')


def write_py_file_with_bad_style(file):
    with open(file, 'w') as f:
        f.write('def main():\tpass\n\n\n \n')


@pytest.fixture()
def repo_with_style_errors(repo_with_style):
    dir = repo_with_style.working_tree_dir
    with zazu.util.cd(dir):
        write_c_file_with_bad_style('temp.c')
        write_c_file_with_bad_style('temp.cc')
        write_c_file_with_bad_style('temp.cpp')
        write_c_file_with_bad_style('temp.hpp')
        write_c_file_with_bad_style('temp.h')
        write_py_file_with_bad_style('temp.py')
    return repo_with_style


@pytest.mark.skipif(not distutils.spawn.find_executable('astyle'),
                    reason="requires astyle")
def test_astyle():
    styler = zazu.plugins.astyle_styler.AstyleStyler(options=['-U'])
    ret = styler.style_string('void main ( ) {}')
    assert ret == 'void main() {}'
    assert styler.default_extensions()


def test_autopep8():
    styler = zazu.plugins.autopep8_styler.Autopep8Styler()
    ret = styler.style_string('def foo ():\n  pass')
    assert ret == 'def foo():\n    pass\n'
    assert ['*.py'] == styler.default_extensions()


@pytest.mark.skipif(not distutils.spawn.find_executable('clang-format'),
                    reason="requires clang-format")
def test_clang_format():
    styler = zazu.plugins.clang_format_styler.ClangFormatStyler(options=['-style=google'])
    ret = styler.style_string('void  main ( ) { }')
    assert ret == 'void main() {}'
    assert styler.default_extensions()


@pytest.mark.skipif(not distutils.spawn.find_executable('clang-format'),
                    reason="requires clang-format")
def test_bad_style(repo_with_style_errors):
    dir = repo_with_style_errors.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['style', '--check', '-v'])
        assert result.exit_code
        assert result.output.endswith('6 files with violations in 6 files\n')
        result = runner.invoke(zazu.cli.cli, ['style', '-v'])
        assert result.exit_code == 0
        assert result.output.endswith('6 files fixed in 6 files\n')
        result = runner.invoke(zazu.cli.cli, ['style', '--check'])
        assert result.exit_code == 0


@pytest.mark.skipif(not distutils.spawn.find_executable('clang-format'),
                    reason="requires clang-format")
def test_dirty_style(repo_with_style_errors):
    dir = repo_with_style_errors.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['style', '--check', '--cached', '-v'])
        assert result.exit_code == 0
        assert result.output == '0 files with violations in 0 files\n'
        repo_with_style_errors.git.add('temp.c')
        result = runner.invoke(zazu.cli.cli, ['style', '--check', '--cached', '-v'])
        assert result.exit_code
        assert result.output.endswith('1 files with violations in 1 files\n')
        result = runner.invoke(zazu.cli.cli, ['style', '--cached', '-v'])
        assert result.output.endswith('1 files fixed in 1 files\n')
        result = runner.invoke(zazu.cli.cli, ['style', '--check', '--cached', '-v'])
        assert not result.exit_code
        assert result.output.endswith('0 files with violations in 1 files\n')
        repo_with_style_errors.git.add('temp.cpp')
        with open('temp.cpp', 'a') as f:
            f.write('//comment\n')
        result = runner.invoke(zazu.cli.cli, ['style', '--cached', '-v'])
        assert result.output.endswith('1 files fixed in 2 files\n')
        # File with missing newline at end of file.
        with open('temp.h', 'a') as f:
            f.write('//comment')
        repo_with_style_errors.git.add('temp.h')
        with open('temp.h', 'a') as f:
            f.write('//another')
        result = runner.invoke(zazu.cli.cli, ['style', '--cached'])
        assert result.output.endswith('File "temp.h" must have a trailing newline\n')


def test_style_no_config(repo_with_missing_style):
    dir = repo_with_missing_style.working_tree_dir
    with zazu.util.cd(dir):
        runner = click.testing.CliRunner()
        result = runner.invoke(zazu.cli.cli, ['style'])
        assert result.output == 'no style settings found\n'
        assert result.exit_code == 0


def test_styler():
    uut = zazu.styler.Styler()
    with pytest.raises(NotImplementedError):
        uut.style_string('')
