# -*- coding: utf-8 -*-
"""style functions for zazu"""

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2016, Lily Robotics"

import glob2 as glob
import multiprocessing
import subprocess
import concurrent.futures
import os


def autopep8_file(file, config, check):
    """checks a single file to see if it is within style guidelines and optionally fixes it"""
    ret = []
    args = ['autopep8']
    args += config.get('options', [])

    check_args = args + ['--diff', file]
    fix_args = args + ['--in-place', file]

    output = subprocess.check_output(check_args)
    if len(output):
        if not check:
            subprocess.check_output(fix_args)
        ret.append(file)
    return ret


def autopep8(files, config, check):
    """Concurrently dispatches multiple workers to perform autopep8"""
    ret = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = {executor.submit(autopep8_file, f, config, check): f for f in files}
        for future in concurrent.futures.as_completed(futures):
            ret += future.result()
    return ret


def astyle(files, config, check):
    """Run astyle on a set of files"""
    ret = []
    if len(files):
        args = ['astyle', '-v']
        args += config.get('options', [])
        if check:
            args.append('--dry-run')
        args += files
        output = subprocess.check_output(args)
        needle = 'Formatted  '
        for l in output.split('\n'):
            if l.startswith(needle):
                ret.append(l[len(needle):])
    return ret


def recursive_glob(pattern):
    """an os optimized recursive glob"""
    if 'nt' == os.name:
        return glob.glob(pattern)
    else:
        try:
            # Expand a glob using sh and ls. This  won't fly on Windows, but it is MUCH faster ~100x than glob2
            ret = subprocess.check_output(['sh -c \"ls -1 {} 2>/dev/null\"'.format(pattern)], shell=True).split('\n')
            ret = [x for x in ret if x]
        except subprocess.CalledProcessError:
            ret = []
        return ret


def glob_with_excludes(pattern, exclude):
    """globs and then excludes certain paths"""
    files = recursive_glob(pattern)

    for e in exclude:
        files = [x for x in files if not x.startswith(e)]
    return files
