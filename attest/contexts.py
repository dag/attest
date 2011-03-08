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
    """Captures standard output and error during the context. Returns a
    tuple of the two streams as lists of lines, added after the context has
    executed.

    ::

        with capture_output() as (out, err):
            print 'Captured'

        assert out == ['Captured']

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
    """Blocks the given `names` from being imported inside the context.
    This is useful for testing import-dependent fallbacks.

    >>> from attest import disable_imports
    >>> with disable_imports('sys'):
    ...     import sys
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
    """Container of metadata for an exception caught by :func:`raises`.

    Attribute access and string adaption is forwarded to the exception
    object. To test the type however you need to use the :attr:`exc`
    attribute directly.

    .. versionadded:: 0.5

    """

    #: The actual exception instance.
    exc = None

    def __getattr__(self, name):
        return getattr(self.exc, name)

    def __str__(self):
        return str(self.exc)

    def __repr__(self):
        return '<Error %s>' % repr(self.exc)


@contextmanager
def raises(*exceptions):
    """Fails if none of the `exceptions` are raised inside the context.
    This reverses failure semantics and is useful for testing code that
    uses exceptions as part of its API.

    ::

        with raises(IOError) as error:
            open('/etc/passwd', 'w')

        assert error.errno == 13

    :param exceptions: Expected exception classes.
    :returns: An :class:`Error` on which the caught exception is set after
        the context has executed, if one was raised.
    :raises AssertionError: If none of the expected exceptions are raised
        in the context.

    .. versionadded:: 0.5

    .. autoclass:: Error
        :members:

    """
    statistics.assertions += 1
    error = Error()
    try:
        yield error
    except exceptions, e:
        error.exc = e
    else:
        exceptions = exceptions[0] if len(exceptions) == 1 else exceptions
        raise AssertionError("didn't raise %s when expected" % _repr(exceptions))
