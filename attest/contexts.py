from contextlib import contextmanager
import sys

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from . import statistics
from .deprecated import _repr


@contextmanager
def capture_output():
    """Context manager capturing standard output and error. Yields a tuple
    of the two streams as lists of lines.

    ::

        with capture_output() as (out, err):
            print 'Captured'

        Assert(out) == ['Captured']

    """
    stdout, stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = StringIO(), StringIO()
    out, err = [], []
    try:
        yield out, err
    finally:
        out.extend(sys.stdout.getvalue().splitlines())
        err.extend(sys.stderr.getvalue().splitlines())
        sys.stdout, sys.stderr = stdout, stderr


@contextmanager
def disable_imports(*names):
    """Context in which imports for `names` raises an :exc:`ImportError`.
    This is useful for testing import-dependent fallbacks.

    >>> from attest import disable_imports
    >>> with disable_imports('sys'): import sys
    ...
    Traceback (most recent call last):
    ImportError: 'sys' is disabled

    .. versionadded:: 0.4

    """
    import __builtin__
    import_ = __builtin__.__import__
    def __import__(name, *args, **kwargs):
        if name in names:
            raise ImportError('%r is disabled' % name)
        return import_(name, *args, **kwargs)
    __builtin__.__import__ = __import__
    try:
        yield
    finally:
        __builtin__.__import__ = import_


class Error(object):

    exc = None

    def __getattr__(self, name):
        return getattr(self.exc, name)

    def __str__(self):
        return str(self.exc)

    def __repr__(self):
        return '<Error %s>' % repr(self.exc)


@contextmanager
def raises(*exceptions):
    statistics.assertions += 1
    error = Error()
    try:
        yield error
    except exceptions, e:
        error.exc = e
    else:
        raise AssertionError('not raises%s' % _repr(exceptions))
