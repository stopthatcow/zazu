# -*- coding: utf-8 -*-
import click
import os
import pytest
import tempfile
import zazu.util
try:
    import __builtin__ as builtins  # NOQA
except ImportError:
    import builtins  # NOQA

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016"


def touch_file(path):
    with open(path, 'w'):
        pass


def test_scan_tree():
    dir = tempfile.mkdtemp()
    exclude_dir = os.path.join(dir, 'exclude')
    os.mkdir(exclude_dir)
    exclude_file = os.path.join(exclude_dir, 'excluded_file.yes')
    include_file = os.path.join(dir, 'file.yes')
    extra_file = os.path.join(dir, 'file.no')
    touch_file(exclude_file)
    touch_file(extra_file)
    results = zazu.util.scantree(dir, ['*.yes'], ['exclude'], exclude_hidden=True)
    assert not results
    touch_file(include_file)
    results = zazu.util.scantree(dir, ['*.yes'], ['exclude'], exclude_hidden=True)
    assert len(results) == 1
    assert os.path.relpath(include_file, dir) in results


def test_pprint_list():
    list = ['a', 'b', 'c']
    formatted = zazu.util.pprint_list(list)
    expected = '\n  - a\n  - b\n  - c'
    assert expected == formatted


def test_raise_uninstalled():
    with pytest.raises(click.ClickException):
        zazu.util.raise_uninstalled('foo')


def test_prompt_default(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda x: '')
    expected = 'bar'
    assert zazu.util.prompt('foo', expected) == expected


def test_prompt_overide_default(monkeypatch):
    expected2 = 'baz'
    monkeypatch.setattr('builtins.input', lambda x: expected2)
    assert zazu.util.prompt('foo', 'bar') == expected2


def test_prompt(monkeypatch):
    expected2 = 'baz'
    monkeypatch.setattr('builtins.input', lambda x: expected2)
    assert zazu.util.prompt('foo') == expected2
    with pytest.raises(ValueError):
        zazu.util.prompt('foo', expected_type=int)


def test_pick_single():
    choices = ['one']
    assert zazu.util.pick(choices, 'foo') == choices[0]


def test_pick(monkeypatch):
    choices = ['one', 'two']
    monkeypatch.setattr('inquirer.prompt', lambda x: {' ': choices[0]})
    assert zazu.util.pick(choices, 'foo') == choices[0]


def test_pick_interupted(monkeypatch):
    choices = ['one', 'two']
    monkeypatch.setattr('inquirer.prompt', lambda x: None)
    with pytest.raises(KeyboardInterrupt):
        zazu.util.pick(choices, 'foo')
