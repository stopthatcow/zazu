# -*- coding: utf-8 -*-
import multiprocessing
import zazu.cmake_helper
import zazu.tool.tool_helper

__author__ = "Nicholas Wiles"
__copyright__ = "Copyright 2017"


def test_arch_to_generator():
    assert 'Unix Makefiles' == zazu.cmake_helper.architecture_to_generator('')


def test_get_toolchain_file_from_arch():
    assert zazu.cmake_helper.get_toolchain_file_from_arch('') is None
    assert zazu.cmake_helper.get_toolchain_file_from_arch('arm32-linux-gnueabihf') is not None


def test_configure_cmake(tmp_dir, mocker):
    mocker.patch('zazu.util.call', return_value=0)
    args = {'ZAZU_BUILD_VERSION': '0.0.0.dev'}
    zazu.cmake_helper.configure(tmp_dir, tmp_dir, 'local', 'release', args, echo=lambda x: x)
    expected_call = [
        'cmake',
        tmp_dir,
        '-G', 'Unix Makefiles', '-DCMAKE_BUILD_TYPE=Release',
        '-DCPACK_SYSTEM_NAME=local', '-DCPACK_PACKAGE_VERSION=0.0.0.dev',
        '-DZAZU_TOOL_PATH={}'.format(zazu.tool.tool_helper.package_path),
        '-DZAZU_BUILD_VERSION=0.0.0.dev'
    ]
    zazu.util.call.assert_called_once_with(expected_call)


def test_build_cmake(tmp_dir, mocker):
    mocker.patch('zazu.util.call', return_value=0)
    zazu.cmake_helper.build(tmp_dir, 'Release', 'foo', True)
    expected_call = [
        'make',
        '-j{}'.format(multiprocessing.cpu_count()),
        'foo',
        'VERBOSE=1'
    ]
    zazu.util.call.assert_called_once_with(expected_call)