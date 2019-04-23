# -*- coding: utf-8 -*-
"""Lazy module importing for zazu."""

from types import ModuleType
import importlib
import sys
try:
    from importlib._bootstrap import _ImportLockContext
    reload = importlib.reload
except (ImportError, AttributeError):
    import imp

    class _ImportLockContext:
        """Python 2 compatible _ImportLockContext."""

        def __enter__(self):
            imp.acquire_lock()

        def __exit__(self, exc_type, exc_value, exc_traceback):
            imp.release_lock()


def nprint(string):
    if False:
        print(string)


def _lazy_import_modules_with_children(base_name, module_name):
    """Recursively setup a tree of LazyModules and return the module corresponding to module_name minus base_name."""
    if base_name == module_name:
        raise ValueError('Base and module can not be the same'.format(base_name))
    if not module_name.startswith(base_name):
        raise ValueError('Module name must start with base name')
    modules = []
    while module_name and module_name != base_name:
        parent, _, leaf_node = module_name.rpartition('.')
        nprint('Lazy module for {}'.format(module_name))
        try:
            module = sys.modules[module_name]
        except KeyError:
            module = LazyModule(module_name)
            sys.modules[module_name] = module
        modules.insert(0, (leaf_node, module))
        module_name = parent
    nprint('Modules in chain: {}'.format(modules))
    for i in range(1, len(modules)):
        leaf_node = modules[i][0]
        parent_module = modules[i-1][1]
        nprint('Setting {} on {}'.format(leaf_node, parent_module.__name__))
        ModuleType.__setattr__(parent_module, leaf_node, modules[i][1])
    return module


def _ensure_loaded(module):
    if not issubclass(type(module), LazyModule):
        nprint('Not a subclass')
        return
    with _ImportLockContext():
        if not ModuleType.__getattribute__(module, '_LAZY_LOAD_PENDING'):
            return
        name = ModuleType.__getattribute__(module, '__name__')
        parent_name, _, remainder = name.rpartition('.')
        nprint('_ensure_loaded on {}'.format(name))
        if parent_name:
            parent_module = sys.modules[parent_name]
            setattr(parent_module, remainder, module)
        if ModuleType.__getattribute__(module, '_LAZY_LOAD_PENDING'):
            reload(module)
            ModuleType.__setattr__(module, '_LAZY_LOAD_PENDING', False)


class LazyModule(ModuleType):
    """Class that imports a module when it is first accessed."""
    _LAZY_LOAD_PENDING = True

    def __getattribute__(self, key):
        try:
            return ModuleType.__getattribute__(self, key)
        except AttributeError:
            pass
        name = ModuleType.__getattribute__(self, '__name__')
        # try:
        #     submodule_name = '.'.join([name, key])
        #     if submodule_name in sys.modules:
        #         nprint('Taking a shortcut to get to {}'.format(key))
        #         return sys.modules['.'.join([name, key])]
        # except KeyError:
        #     pass
        if ModuleType.__getattribute__(self, '_LAZY_LOAD_PENDING'):
            _ensure_loaded(self)
        return ModuleType.__getattribute__(self, key)

    def __setattr__(self, key, value):
        name = ModuleType.__getattribute__(self, '__name__')
        if ModuleType.__getattribute__(self, '_LAZY_LOAD_PENDING'):
            nprint("__setattr__ on {}".format(name))
            _ensure_loaded(self)
        ModuleType.__setattr__(self, key, value)


def lazy_import(scope, imports):
    """Declare a list of modules to import on their first use.

    Args:
        scope: the scope to import the modules into.
        imports: the list of modules to import.

    """
    with _ImportLockContext():
        for m in imports:
            nprint('lazy import {}'.format(m))
            base_name, _, remainder = m.partition('.')
            if base_name not in scope:
                nprint('Inserting new lazy chain as {}'.format(base_name))
                scope[base_name] = _lazy_import_modules_with_children('', m)
                continue
            existing_module = scope[base_name]
            nprint('Founding existing module in scope for {}'.format(base_name))
            while base_name != m:
                leaf_name, _, remainder = remainder.partition('.')
                nprint('leaf_name now {}'.format(leaf_name))
                try:
                    nprint('Looking for child of {} at {}'.format(base_name, leaf_name))
                    existing_module = ModuleType.__getattribute__(existing_module, leaf_name)
                    nprint('Found child at {} {}'.format(base_name, leaf_name))

                except AttributeError:
                    nprint('Did not find child of {} at {}'.format(base_name, leaf_name))
                    ModuleType.__setattr__(existing_module, leaf_name,  _lazy_import_modules_with_children(base_name, m))
                    nprint('Setting {} {}'.format(base_name, leaf_name))
                    break
                base_name = '.'.join([base_name, leaf_name])
                nprint('base_name now {}'.format(base_name))
