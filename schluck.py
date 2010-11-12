# coding:utf-8
from __future__ import with_statement

import sys
import traceback
from functools import wraps
import inspect
from contextlib import contextmanager

try:
    from abc import ABCMeta, abstractmethod
except ImportError:
    ABCMeta = type
    abstractmethod = lambda x: x


class AbstractFormatter(object):
    """Optional base for formatters, serves as documentation and improves
    errors for incomplete formatters.

    :param tests: The list of test functions we will be running.

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, tests):
        raise NotImplementedError

    @abstractmethod
    def success(self, test):
        """When a test succeeds, this method is called with the test
        function.

        """
        raise NotImplementedError

    @abstractmethod
    def failure(self, test, error, traceback):
        """When a test fails, this method is called with the test
        function, the exception instance that was raised,
        and a cleaned up traceback string.

        """
        raise NotImplementedError

    @abstractmethod
    def finished(self):
        """Called when all tests have run."""
        raise NotImplementedError


class PlainFormatter(AbstractFormatter):
    """Plain text ASCII output for humans."""

    def __init__(self, tests):
        self.total = len(tests)
        self.failures = []

    def success(self, test):
        sys.stdout.write('.')
        sys.stdout.flush()

    def failure(self, test, error, traceback):
        if isinstance(error, AssertionError):
            sys.stdout.write('F')
        else:
            sys.stdout.write('E')
        sys.stdout.flush()
        self.failures.append((test, traceback))

    def finished(self):
        print
        for test, trace in self.failures:
            print '-' * 80
            print '.'.join((test.__module__, test.__name__))
            if test.__doc__:
                print inspect.getdoc(test)
            print '-' * 80
            print trace
            print

        print 'Failures: %s/%s' % (len(self.failures), self.total)


class FancyFormatter(AbstractFormatter):
    """Heavily uses ANSI escape codes for fancy output to 256-color
    terminals. Progress of running the tests is indicated by a progressbar
    and failures are shown with syntax highlighted tracebacks.

    This is the default formatter.

    """

    def __init__(self, tests):
        from progressbar import ProgressBar
        self.counter = 0
        self.progress = ProgressBar(maxval=len(tests))
        self.progress.start()
        self.failures = []

    def success(self, test):
        self.counter += 1
        self.progress.update(self.counter)

    def failure(self, test, error, traceback):
        self.counter += 1
        self.progress.update(self.counter)
        self.failures.append((test, traceback))

    def finished(self):
        from pygments.console import colorize
        from pygments import highlight
        from pygments.lexers import PythonTracebackLexer
        from pygments.formatters import Terminal256Formatter

        self.progress.finish()
        for test, trace in self.failures:
            print '—' * 80
            print colorize('bold', '.'.join((test.__module__, test.__name__)))
            if test.__doc__:
                print inspect.getdoc(test)
            print '—' * 80
            print highlight(trace, PythonTracebackLexer(),
                            Terminal256Formatter())

        if self.failures:
            failed = colorize('red', str(len(self.failures)))
        else:
            failed = len(self.failures)
        print 'Failures: %s/%s' % (failed, self.counter)


class Tests(object):
    """Collection of test functions."""

    def __init__(self):
        self.tests = []
        self._context = None

    def test(self, func):
        """Decorate a function as a test belonging to this collection."""
        @wraps(func)
        def wrapper():
            if self._context is None:
                func()
            else:
                with self._context() as context:
                    if len(inspect.getargspec(func)[0]) != 0:
                        func(*context)
                    else:
                        func()
        self.tests.append(wrapper)
        return wrapper

    def context(self, func):
        """Decorate a function as a :func:`~contextlib.contextmanager`
        for running the tests in this collection in. Corresponds to setup
        and teardown in other testing libraries.

        ::

            db = Tests()

            @db.context
            def connect():
                con = connect_db()
                try:
                    yield con,
                finally:
                    con.disconnect()

            @db.test
            def using_connection(con):
                Assert(con).is_not(None)

        The above corresponds to::

            db = Tests()

            def connect():
                con = connect_db()
                try:
                    yield con
                finally:
                    con.disconnect()

            @db.test
            def using_connection():
                with connect() as con:
                    Assert(con).is_not(None)

        The difference is that this decorator applies the context to all
        tests defined after it, so it's less repetitive. Note that you need
        to yield either a tuple or nothing. The tuple is splatted as the
        arguments to the test function - unless it doesn't take any arguments.

        """
        func = contextmanager(func)
        self._context = func
        return func

    def register(self, tests):
        """Merge in another test collection."""
        self.tests.extend(tests.tests)

    def run(self, formatter=FancyFormatter):
        """Run all tests in this collection.

        :param formatter:
            A class implementing :class:`AbstractFormatter` (not enforced).

        """
        failed = False
        formatter = formatter(self.tests)
        for test in self.tests:
            try:
                test()
            except Exception, e:
                failed = True
                lines = traceback.format_exc().splitlines()
                clean = lines[0:1]
                stack = iter(lines[1:-1])  # stack traces are in the middle
                # loop two lines at a time
                for first, second in zip(stack, stack):
                    # only keep if this file is not the source of the trace
                    if __file__[0:-1] not in first:
                        clean.extend((first, second))
                clean.append(lines[-1])
                formatter.failure(test, e, '\n'.join(clean))
            else:
                formatter.success(test)
        formatter.finished()
        if failed:
            raise SystemExit(1)


class Assert(object):
    """Wrap an object such that boolean operations on it fails with an
    :exc:`AssertionError` if the operation results in :const:`False`,
    with more helpful error messages on failure than :keyword:`assert`.

    A test failure is simply an unhandled exception, so it is completely
    optional to use this class.

    Examples::

        Assert(1 + 1) == 2
        2 in Assert([1, 2, 3])

    Attributes are proxied to the wrapped object, returning the result
    wrapped as well::

        hello = Assert('hello')
        hello == 'hello'
        hello.upper() == 'HELLO'
        hello.capitalize() == 'Hello'

    Used in boolean context, fails if non-true. These all fail::

        bool(Assert(0))
        if Assert(0): pass
        assert Assert(0)

    Identical to, except for the more helpful failure message::

        Assert(bool(0)) == True

    """

    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, obj):
        assert self.obj == obj, '%r != %r' % (self.obj, obj)

    def __ne__(self, obj):
        assert self.obj != obj, '%r == %r' % (self.obj, obj)

    def is_(self, obj):
        """The :keyword:`is` operator is not overridable, for good reasons
        (that would defeat its purpose), so you can use this method for
        asserting identity::

            Assert(True).is_(True)

        """
        assert self.obj is obj, '%r is not %r' % (self.obj, obj)

    def is_not(self, obj):
        """The negated form of :meth:`is_`, corresponding to the ``is not``
        operation::

            Assert([]).is_not([])

        """
        assert self.obj is not obj, '%r is %r' % (self.obj, obj)

    def __contains__(self, obj):
        assert obj in self.obj, '%r not in %r' % (obj, self.obj)

    def in_(self, obj):
        """Assert membership. While you can use the :keyword:`in` operator,
        its order is inconsistent with the rest of the operators and doesn't
        work with the ``not in`` operation.

        ::

            2 in Assert([1, 2, 3])
            Assert(2).in_([1, 2, 3])

        """
        assert self.obj in obj, '%r not in %r' % (self.obj, obj)

    def not_in(self, obj):
        """The negated form of :meth:`in_`, corresponding to the ``not in``
        operation::

            Assert(0).not_in([1, 2, 3])

        """
        assert self.obj not in obj, '%r in %r' % (self.obj, obj)

    def __lt__(self, obj):
        assert self.obj < obj, '%r >= %r' % (self.obj, obj)

    def __le__(self, obj):
        assert self.obj <= obj, '%r > %r' % (self.obj, obj)

    def __gt__(self, obj):
        assert self.obj > obj, '%r <= %r' % (self.obj, obj)

    def __ge__(self, obj):
        assert self.obj >= obj, '%r < %r' % (self.obj, obj)

    def __nonzero__(self):
        assert self.obj, 'not %r' % self.obj
        return True

    @staticmethod
    @contextmanager
    def raises(exception):
        """Context manager that fails if a particular exception is not
        raised::

            with Assert.raises(TypeError):
                max(5)

        :param exception: An exception class.

        """
        try:
            yield
        except exception:
            pass
        else:
            error = exception.__name__
            raise AssertionError("didn't raise %s" % error)

    def __getattr__(self, name):
        return Assert(getattr(self.obj, name))

    def __call__(self, *args, **kwargs):
        return Assert(self.obj(*args, **kwargs))

    def __repr__(self):
        return 'Assert(%r)' % self.obj
