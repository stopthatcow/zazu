# -*- coding: utf-8 -*-
"""Lazy module importing for zazu."""

from types import ModuleType, MethodType
import importlib
import sys
try:
    from importlib._bootstrap import _ImportLockContext
except ImportError:
    import imp

    class _ImportLockContext:
        """Python 2 compatible _ImportLockContext."""

        def __enter__(self):
            imp.acquire_lock()

        def __exit__(self, exc_type, exc_value, exc_traceback):
            imp.release_lock()


def _lazy_import(module):
    old_getattribute = LazyModule.__getattribute__
    old_setattr = LazyModule.__setattr__
    name = module.__name__
    #print('__getattribute__ on {}'.format(name))
    try:
        #print('  Importing {}'.format(name))
        imported_module_dict = importlib.import_module(name).__dict__
        LazyModule.__getattribute__ = ModuleType.__getattribute__
        LazyModule.__setattr__ = ModuleType.__setattr__
        module.__dict__.update(imported_module_dict)
        module.__getattribute__ = MethodType(ModuleType.__getattribute__, module)
        module.__setattr__ = MethodType(ModuleType.__setattr__, module)
    finally:
        #print('  Finish importing {}'.format(name))
        LazyModule.__getattribute__ = old_getattribute
        LazyModule.__setattr__ = old_setattr


class LazyModule(ModuleType):
    """Class that imports a module when it is first accessed."""

    def __getattribute__(self, key):
        if key not in ('__name__', '__class_'):
            try:
                return sys.modules['.'.join([self.__name__, key])]
            except KeyError:
                pass
            _lazy_import(self)
        return ModuleType.__getattribute__(self, key)

    def __setattr__(self, key, value):
        _lazy_import(self)
        return ModuleType.__setattr__(self, key, value)


def lazy_import(scope, imports):
    """Declare a list of modules to import on their first use.

    Args:
        scope: the scope to import the modules into.
        imports: the list of modules to import.

    """
    for m in imports:
        with _ImportLockContext():
            #print('Lazy_importing {}'.format(m))
            module_path = m.split('.')
            target_dict = scope
            for i, component in enumerate(module_path[:-1]):
                parent_name = '.'.join(module_path[:i+1])
                if component in target_dict:
                    #print('Found existing {} in scope'.format(component))
                    # if parent_name in sys.modules:
                        #print('Found existing {} in sys.modules'.format(component))
                    next_obj = target_dict[component] if parent_name not in sys.modules else sys.modules[parent_name]
                else:
                    #print('Parent "{}" imported'.format(parent_name))
                    next_obj = importlib.import_module(parent_name) if parent_name not in sys.modules else sys.modules[parent_name]
                target_dict[component] = next_obj
                target_dict = next_obj.__dict__
            target_dict[module_path[-1]] = LazyModule(m) if m not in sys.modules else sys.modules[m]
