import sys

from contextlib import contextmanager
from shutil     import rmtree
from tempfile   import mkdtemp

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO  import StringIO

from attest            import statistics
from attest.deprecated import _repr


__all__ = ['capture_output',
           'disable_imports',
           'Error',
           'raises',
           'tempdir',
           'warns',
          ]


@contextmanager
def capture_output():
    """Captures standard output and error during the context. Returns a
    tuple of the two streams as lists of lines, added after the context has
    executed.

    .. testsetup::

        from attest import capture_output

    >>> with capture_output() as (out, err):
    ...    print 'Captured'
    ...
    >>> out
    ['Captured']

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

    .. testsetup::

        from attest import disable_imports

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
        return u'<Error %s>' % repr(self.exc)


@contextmanager
def raises(*exceptions):
    """Fails if none of the `exceptions` are raised inside the context.
    This reverses failure semantics and is useful for testing code that
    uses exceptions as part of its API.

    .. testsetup::

        from attest import raises

    >>> with raises(IOError) as error:
    ...    open('/etc/passwd', 'w')
    ...
    >>> error.errno
    13

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


@contextmanager
def tempdir(*args, **kwargs):
    """Creates a temporary directory, removing it and everything in it when
    the context exits. For files you can use
    :func:`~tempfile.TemporaryFile` as a context manager.

    Returns the path to the directory. Arguments are passed to
    :func:`~tempfile.mkdtemp`.

    .. versionadded:: 0.6

    """
    d = mkdtemp(*args, **kwargs)
    try:
        yield d
    finally:
        rmtree(d)


@contextmanager
def warns(*warnings, **opts):
    """Context manager that succeeds if all `warnings` are issued inside the
    context. Yields a list of matching captured warnings as exception objects.

    .. testsetup::

        from attest import warns
        import warnings

    >>> with warns(UserWarning) as captured:
    ...     warnings.warn("Example warning", UserWarning)
    ...
    >>> unicode(captured[0]) == "Example warning"
    True

    :param any: Require only *one* of the warnings to be issued (rather than
        all).

    .. note::

        :mod:`warnings` filtering is overridden to ``"always"`` for monitored
        warnings.

    """
    import warnings as warnings_

    captured = []
    old_filters, old_showwarning = warnings_.filters, warnings_.showwarning
    warnings_.filters = old_filters[:]

    def showwarning(message, category, *args, **kwargs):
        if category not in warnings:
            old_showwarning(message, category, *args, **kwargs)
            return
        captured.append(message)
    warnings_.showwarning = showwarning

    for warning in warnings:
        warnings_.simplefilter("always", warning)

    try:
        yield captured
        if opts.get("any", False):
            assert captured
        else:
            assert set(warnings) == set(map(type, captured))
    finally:
        warnings_.filters = old_filters
        warnings_.showwarning = old_showwarning
