# -*- coding: utf-8 -*-
"""Lazy module importing for zazu."""

import imp
import importlib
import sys
from types import ModuleType
try:
    reload = importlib.reload
except AttributeError:
    pass


class _ImportLockContext:
    """Context manager to aquire and release the import lock."""

    def __enter__(self):
        imp.acquire_lock()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        imp.release_lock()


def _lazy_import_modules_with_children(base_name, remainder):
    """Recursively ensure that all modules downstream of base_name are present in sys.modules and linked to children.

    These modules may either be real modules or _LazyModules and linked to their children defined by remainder.

    """
    leaf_name, _, remainder = remainder.partition('.')
    module_name = '.'.join([base_name, leaf_name]) if base_name else leaf_name
    try:
        module = sys.modules[module_name]
    except KeyError:
        module = _LazyModule(module_name)
        sys.modules[module_name] = module
    if remainder:
        child = _lazy_import_modules_with_children(module_name, remainder)
        leaf_name, _, remainder = remainder.partition('.')
        ModuleType.__setattr__(module, leaf_name, child)
    return module


def _ensure_loaded(module):
    """Recursively ensure that a module and its parents are loaded."""
    with _ImportLockContext():
        if not ModuleType.__getattribute__(module, '_LAZY_LOAD_PENDING'):
            return
        name = module.__name__
        parent_name, _, remainder = name.rpartition('.')
        if parent_name:
            parent_module = sys.modules[parent_name]
            # This may invoke _ensure_loaded() if parent_module is an unloaded _LazyModule.
            setattr(parent_module, remainder, module)
        if ModuleType.__getattribute__(module, '_LAZY_LOAD_PENDING'):
            reload(module)
            ModuleType.__setattr__(module, '_LAZY_LOAD_PENDING', False)


class _LazyModule(ModuleType):
    """Class that imports a module when it is first accessed."""
    _LAZY_LOAD_PENDING = True

    def __getattribute__(self, key):
        try:
            return ModuleType.__getattribute__(self, key)
        except AttributeError:
            pass
        _ensure_loaded(self)
        return ModuleType.__getattribute__(self, key)

    def __setattr__(self, key, value):
        _ensure_loaded(self)
        ModuleType.__setattr__(self, key, value)


def lazy_import(scope, imports):
    """Declare a list of modules to import on their first use.

    Args:
        scope: the scope to import the modules into.
        imports: the list of modules to import.

    """
    with _ImportLockContext():
        for module_name in imports:
            base_name, _, remainder = module_name.partition('.')
            if base_name not in scope:
                scope[base_name] = _lazy_import_modules_with_children('', module_name)
                continue
            existing_module = scope[base_name]
            while base_name != module_name:
                leaf_name, _, new_remainder = remainder.partition('.')
                try:
                    existing_module = ModuleType.__getattribute__(existing_module, leaf_name)
                except AttributeError:
                    new_module = _lazy_import_modules_with_children(base_name, remainder)
                    ModuleType.__setattr__(existing_module, leaf_name, new_module)
                    break
                base_name = '.'.join([base_name, leaf_name])
                remainder = new_remainder
