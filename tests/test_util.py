# -*- coding: utf-8 -*-
import os
import tempfile
import zazu.util

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
