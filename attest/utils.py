import sys

from array      import array
from contextlib import contextmanager
from inspect    import getmembers
from pkgutil    import iter_modules
from six        import reraise


__all__ = ['get_terminal_size',
           'import_dotted_name',
           'deep_iter_modules',
           'deep_get_members',
           'parse_options',
           'nested',
           'counter']


def get_terminal_size(default=(80, 24)):
    """Try to get the size of the terminal as a tuple ``(width, height)``
    falling back on `default`.

    .. versionadded:: 0.6

    """
    try:
        import fcntl, termios
    except ImportError:
        return default
    try:
        ary = array('h', fcntl.fcntl(sys.stdin, termios.TIOCGWINSZ, chr(0) * 8))
        return ary[1], ary[0]
    except IOError:
        return default


def import_dotted_name(name):
    """Get an object by its "dotted name", a string representing its import
    location. The last dot can also be a colon instead.

    .. versionadded:: 0.6

    """
    name = str(name)
    if ':' in name:
        module, obj = name.split(':', 1)
    elif '.' in name:
        module, obj = name.rsplit('.', 1)
    else:
        return __import__(name, level=0)
    mod = __import__(module, fromlist=[obj], level=0)
    return getattr(mod, obj)


def deep_iter_modules(name):
    """Iterate over all modules under an import name. Like
    :func:`~pkgutil.iter_modules` but recursive, and yielding the dotted
    names of each module.

    .. versionadded:: 0.6

    """
    mod = import_dotted_name(name)
    yield name
    if not hasattr(mod, '__path__'):
        return
    for _, name, _ in iter_modules(mod.__path__, name + '.'):
        for name in deep_iter_modules(name):
            yield name


def deep_get_members(name, predicate=None, private=False):
    """Get all top-level objects in all modules under `name` satisfying
    `predicate` if provided, ignoring private modules and objects unless
    `private` is true.

    .. versionadded:: 0.6

    """
    seen = set()
    for name in deep_iter_modules(name):
        mod = import_dotted_name(name)
        name = name.rsplit('.', 1)[-1]
        if not private and name.startswith('_'):
            continue
        for name, value in getmembers(mod, predicate):
            if id(value) in seen or not private and name.startswith('_'):
                continue
            yield value
            seen.add(id(value))


def parse_options(args):
    types = dict(yes=True, no=False, on=True, off=False,
                 true=True, false=False, none=None)

    def parse_key(key):
        return key.strip().replace('-', '_')

    def parse_value(value):
        value = value.strip()

        if not value:
            return

        if value in types:
            return types[value]

        if ',' in value:
            seq = tuple(map(parse_value, value.split(',')))
            if all(isinstance(v, dict) for v in seq):
                d = {}
                for v in seq:
                    d.update(v)
                return d
            return seq

        if ':' in value:
            return dict([map(parse_value, value.split(':', 1))])

        try:
            return int(value)
        except ValueError:
            return value

    def parse_option(option):
        key, value = option.split('=', 1)
        key, value = parse_key(key), parse_value(value)
        return key, value

    args = [arg for arg in args if '=' in arg]
    opts = dict(map(parse_option, args))
    return opts


@contextmanager
def nested(constructors):
    exc = None, None, None
    args = []
    exits = []
    try:
        for constructor in constructors:
            manager = constructor()
            args.append(manager.__enter__())
            exits.append(manager.__exit__)
        yield args
    except:
        exc = sys.exc_info()
    finally:
        for exit in reversed(exits):
            try:
                if exit(*exc):
                    exc = None, None, None
            except:
                exc = sys.exc_info()
        if exc != (None, None, None):
            reraise(*exc)


class counter(dict):
    def increment(self, key):
        if key not in self:
            self[key] = 1
        else:
            self[key] += 1
        return self[key]
