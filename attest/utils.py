import sys
from array import array
from pkgutil import iter_modules
from inspect import getmembers


def get_terminal_size(default=(80, 24)):
    """Try to get the size of the terminal as a tuple ``(width, height)``
    falling back on `default`.

    .. versionadded:: 0.6

    """
    try:
        import fcntl, termios
    except ImportError:
        return default
    ary = array('h', fcntl.ioctl(sys.stdin, termios.TIOCGWINSZ, chr(0) * 8))
    return ary[1], ary[0]


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
        return __import__(name)
    mod = __import__(module, fromlist=[obj])
    return getattr(mod, obj)


def deep_iter_modules(name):
    """Iterate over all modules under an import name. Like
    :func:`~pkgutil.iter_modules` but recursive, and yielding the dotted
    names of each module.

    .. versionadded:: 0.6

    """
    mod = import_dotted_name(name)
    if not hasattr(mod, '__path__'):
        yield name
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
            if all(isinstance(v, tuple) for v in seq):
                return dict(seq)
            return seq

        if ':' in value:
            return tuple(map(parse_value, value.split(':', 1)))

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
