"""Tools for doing dynamic imports Modified from https://github.com/PEAK-Legacy/Importing."""

__all__ = [
    'lazyModule', 'joinPath', 'whenImported', 'getModuleHooks',
]

from types import ModuleType
try:
    from types import StringTypes
except ImportError:
    StringTypes = str
from sys import modules
from imp import acquire_lock, release_lock


class AlreadyRead(Exception):
    pass


try:
    exec("def reraise(t, v, tb): raise t, v, tb")
except SyntaxError:
    def reraise(t, v, tb):
        if v is None:
            v = t()
        if v.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value


def joinPath(modname, relativePath):
    """Adjust a module name by a '/'-separated, relative or absolute path."""

    module = modname.split('.')
    for p in relativePath.split('/'):

        if p == '..':
            module.pop()
        elif not p:
            module = []
        elif p != '.':
            module.append(p)

    return '.'.join(module)


def lazyModule(modname, relativePath=None):
    """Return module 'modname', but with its contents loaded "on demand".

    This function returns 'sys.modules[modname]', if present.  Otherwise
    it creates a 'LazyModule' object for the specified module, caches it
    in 'sys.modules', and returns it.

    'LazyModule' is a subclass of the standard Python module type, that
    remains empty until an attempt is made to access one of its
    attributes.  At that moment, the module is loaded into memory, and
    any hooks that were defined via 'whenImported()' are invoked.

    Note that calling 'lazyModule' with the name of a non-existent or
    unimportable module will delay the 'ImportError' until the moment
    access is attempted.  The 'ImportError' will occur every time an
    attribute access is attempted, until the problem is corrected.

    This function also takes an optional second parameter, 'relativePath',
    which will be interpreted as a '/'-separated path string relative to
    'modname'.  If a 'relativePath' is supplied, the module found by
    traversing the path will be loaded instead of 'modname'.  In the path,
    '.' refers to the current module, and '..' to the current module's
    parent.  For example::

        fooBaz = lazyModule('foo.bar','../baz')

    will return the module 'foo.baz'.  The main use of the 'relativePath'
    feature is to allow relative imports in modules that are intended for
    use with module inheritance.  Where an absolute import would be carried
    over as-is into the inheriting module, an import relative to '__name__'
    will be relative to the inheriting module, e.g.::

        something = lazyModule(__name__,'../path/to/something')

    The above code will have different results in each module that inherits
    it.

    (Note: 'relativePath' can also be an absolute path (starting with '/');
    this is mainly useful for module '__bases__' lists.)

    """

    def _loadModule(module):
        acquire_lock()  # This is the main change from the PEAK version. They didn't protect these first 8 lines.
        oldGA = LazyModule.__getattribute__
        oldSA = LazyModule.__setattr__

        modGA = ModuleType.__getattribute__
        modSA = ModuleType.__setattr__

        LazyModule.__getattribute__ = modGA
        LazyModule.__setattr__ = modSA

        try:
            try:
                # don't reload if already loaded!
                if module.__dict__.keys() == ['__name__']:
                    # Get Python to do the real import!
                    reload(module)
                try:
                    for hook in getModuleHooks(module.__name__):
                        hook(module)
                finally:
                    # Ensure hooks are not called again, even if they fail
                    postLoadHooks[module.__name__] = None
            except:
                # Reset our state so that we can retry later
                if '__file__' not in module.__dict__:
                    LazyModule.__getattribute__ = oldGA.im_func
                    LazyModule.__setattr__ = oldSA.im_func
                raise

            try:
                # Convert to a real module (if under 2.2)
                module.__class__ = ModuleType
            except TypeError:
                pass    # 2.3 will fail, but no big deal

        finally:
            release_lock()

    class LazyModule(ModuleType):
        __slots__ = ()

        def __init__(self, name):
            ModuleType.__setattr__(self, '__name__', name)
            # super(LazyModule,self).__init__(name)

        def __getattribute__(self, attr):
            _loadModule(self)
            return ModuleType.__getattribute__(self, attr)

        def __setattr__(self, attr, value):
            _loadModule(self)
            return ModuleType.__setattr__(self, attr, value)

    if relativePath:
        modname = joinPath(modname, relativePath)

    acquire_lock()
    try:
        if modname not in modules:
            getModuleHooks(modname)  # force an empty hook list into existence
            modules[modname] = LazyModule(modname)
            if '.' in modname:
                # ensure parent module/package is in sys.modules
                # and parent.modname=module, as soon as the parent is imported
                splitpos = modname.rindex('.')
                whenImported(
                    modname[:splitpos],
                    lambda m: setattr(m, modname[splitpos+1:], modules[modname])
                )
        return modules[modname]
    finally:
        release_lock()


postLoadHooks = {}


def getModuleHooks(moduleName):
    """Get list of hooks for 'moduleName'; error if module already loaded."""

    acquire_lock()
    try:
        hooks = postLoadHooks.setdefault(moduleName, [])
        if hooks is None:
            raise AlreadyRead("Module already imported", moduleName)
        return hooks
    finally:
        release_lock()


def _setModuleHook(moduleName, hook):
    acquire_lock()
    try:
        if moduleName in modules and postLoadHooks.get(moduleName) is None:
            # Module is already imported/loaded, just call the hook
            module = modules[moduleName]
            hook(module)
            return module

        getModuleHooks(moduleName).append(hook)
        return lazyModule(moduleName)
    finally:
        release_lock()


def whenImported(moduleName, hook=None):
    """Call 'hook(module)' when module named 'moduleName' is first used.

    'hook' must accept one argument: the module object named by 'moduleName',
    which must be a fully qualified (i.e. absolute) module name.  The hook
    should not raise any exceptions, or it may prevent later hooks from
    running.

    If the module has already been imported normally, 'hook(module)' is
    called immediately, and the module object is returned from this function.
    If the module has not been imported, or has only been imported lazily,
    then the hook is called when the module is first used, and a lazy import
    of the module is returned from this function.  If the module was imported
    lazily and used before calling this function, the hook is called
    immediately, and the loaded module is returned from this function.

    Note that using this function implies a possible lazy import of the
    specified module, and lazy importing means that any 'ImportError' will be
    deferred until the module is used.

    """
    if hook is None:
        def decorate(func):
            whenImported(moduleName, func)
            return func
        return decorate

    if '.' in moduleName:
        # If parent is not yet imported, delay hook installation until the
        # parent is imported.
        splitpos = moduleName.rindex('.')
        whenImported(
            moduleName[:splitpos], lambda m: _setModuleHook(moduleName, hook)
        )
    else:
        return _setModuleHook(moduleName, hook)
