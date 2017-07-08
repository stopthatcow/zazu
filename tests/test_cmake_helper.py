# -*- coding: utf-8 -*-
import multiprocessing
import zazu.cmake_helper

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


def test_arch_to_generator():
    assert 'Unix Makefiles' == zazu.cmake_helper.architecture_to_generator('')


def test_configure_cmake(tmp_dir, mocker):
    mocker.patch('zazu.util.call', return_value=0)
    args = {'ZAZU_BUILD_VERSION': '0.0.0.dev'}
    zazu.cmake_helper.configure(tmp_dir, tmp_dir, 'host', 'release', args, echo=lambda x: x)
    expected_call = [
        'cmake',
        tmp_dir,
        '-G', 'Unix Makefiles', '-DCMAKE_BUILD_TYPE=Release',
        '-DCPACK_SYSTEM_NAME=host', '-DCPACK_PACKAGE_VERSION=0.0.0.dev',
        '-DZAZU_BUILD_VERSION=0.0.0.dev'
    ]
    zazu.util.call.assert_called_once_with(expected_call)
    # Call again to ensure we cache the args.
    zazu.cmake_helper.configure(tmp_dir, tmp_dir, 'host', 'release', args, echo=lambda x: x)
    zazu.util.call.assert_called_once()


def test_build_cmake_posix(tmp_dir, mocker):
    mocker.patch('zazu.util.call', return_value=0)
    mocker.patch('os.name', new_callable=mocker.PropertyMock(return_value='posix'))
    zazu.cmake_helper.build(tmp_dir, 'arm32-linux-gnueabihf', 'Release', 'foo', True)
    expected_call = [
        'make',
        '-j{}'.format(multiprocessing.cpu_count()),
        'foo',
        'VERBOSE=1'
    ]
    zazu.util.call.assert_called_once_with(expected_call)


def test_build_cmake_windows(tmp_dir, mocker):
    mocker.patch('zazu.util.call', return_value=0)
    zazu.cmake_helper.build(tmp_dir, 'x86_64-win-msvc_2015', 'Release', 'foo', True)
    expected_call = [
        'cmake',
        '--build'.format(multiprocessing.cpu_count()),
        '.',
        '--config', 'Release',
        '--target', 'foo'
    ]
    zazu.util.call.assert_called_once_with(expected_call)
