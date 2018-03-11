# -*- coding: utf-8 -*-
import click
import functools
import inquirer
import os
import pytest
import subprocess
import tempfile
import time
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


def test_check_output(mocker):
    mocker.patch('subprocess.check_output', side_effect=OSError(''))
    with pytest.raises(click.ClickException):
        zazu.util.check_output(['foo'])
        subprocess.check_output.assert_called_once_with(['foo'])


def test_call(mocker):
    mocker.patch('subprocess.call', side_effect=OSError(''))
    with pytest.raises(click.ClickException):
        zazu.util.call(['foo'])
        subprocess.call.assert_called_once_with(['foo'])


def test_check_popen_not_found(mocker):
    mocker.patch('subprocess.Popen', side_effect=OSError(''))
    with pytest.raises(click.ClickException):
        zazu.util.check_popen(['foo'])
        subprocess.call.assert_called_once_with(['foo'])


def test_check_popen(mocker):
    mocked_process = mocker.Mock()
    mocked_process.communicate = mocker.Mock(return_value=('out', 'err'))
    mocker.patch('subprocess.Popen', return_value=mocked_process)
    mocked_process.returncode = 0
    assert 'out' == zazu.util.check_popen(stdin_str='input', args=['foo'])
    subprocess.Popen.assert_called_once_with(args=['foo'], stderr=subprocess.PIPE,
                                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    mocked_process.communicate.assert_called_once_with('input')
    with pytest.raises(subprocess.CalledProcessError) as e:
        mocked_process.returncode = 1
        zazu.util.check_popen(stdin_str='input', args=['foo'])
    assert e.value.returncode == 1
    assert e.value.cmd == ['foo']
    assert e.value.output == 'err'


def call(*args, **kwargs):
    try:
        return subprocess.call(*args, **kwargs)
    except OSError:
        raise_uninstalled(args[0][0])


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


def test_pick_empty():
    assert zazu.util.pick([], 'foo') is None


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


UNFLATTENED_DICT = {'a': {'b': {'c': 5}, 'd': 6}}
FLATTENED_DICT = {'a.b.c': 5, 'a.d': 6}


def test_flatten_dict():
    assert FLATTENED_DICT == zazu.util.flatten_dict(UNFLATTENED_DICT)


def test_unflatten_dict():
    assert UNFLATTENED_DICT == zazu.util.unflatten_dict(FLATTENED_DICT)


def test_dict_get_nested():
    d = {'a': {'b': 's', 'c': {'d': 'e'}}}
    assert zazu.util.dict_get_nested(d, ['a', 'b'], None) == 's'
    assert zazu.util.dict_get_nested(d, ['a', 'c'], None) == {'d': 'e'}
    assert zazu.util.dict_get_nested(d, ['a', 'c', 'e'], None) is None


def test_dict_del_nested():
    d = {'a': {'b': 's', 'c': {'d': 'e'}}}
    zazu.util.dict_del_nested(d, ['a', 'b'])
    assert d == {'a': {'c': {'d': 'e'}}}
    zazu.util.dict_del_nested(d, ['a'])
    assert d == {}


def test_dict_update_nested():
    d = {'a': {'b': 's', 'c': {'d': 'e'}}}
    zazu.util.dict_update_nested(d, {'a': {'b': {'c': 'd'}}})
    assert d == {'a': {'b': {'c': 'd'}, 'c': {'d': 'e'}}}


def test_readline_fallback(mocker):
    old_import = __import__

    def new_import(*args, **kwargs):
        if args[0] == 'readline':
            raise ImportError
        elif args[0] == 'pyreadline':
            pass
        else:
            return old_import(*args, **kwargs)

    mocker.patch('__builtin__.__import__', side_effect=new_import)
    reload(zazu.util)
    imports = [arg[0][0] for arg in builtins.__import__.call_args_list]
    assert 'readline' in imports
    assert 'pyreadline' in imports


def test_cd(tmp_dir):
    old_dir = os.getcwd()
    with zazu.util.cd(tmp_dir):
        assert os.path.realpath(os.getcwd()) == os.path.realpath(tmp_dir)
    assert os.getcwd() == old_dir


def test_dispatch():
    def wait(t):
        time.sleep(t)
        return t
    times = [0.1, 0.2, 0.3]
    work = [functools.partial(wait, t) for t in times]
    start_time = time.time()
    assert sorted(zazu.util.dispatch(work)) == sorted(times)
    time_taken = time.time() - start_time
    assert time_taken < sum(times)
