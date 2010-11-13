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
        print
        for test, trace in self.failures:
            if test.__module__ == '__main__':
                print test.__name__
            else:
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
        from progressbar import ProgressBar, Percentage, Bar, ETA, SimpleProgress
        widgets = [SimpleProgress(), ' [', ETA(), Bar(), Percentage(), ']']
        self.counter = 0
        self.progress = ProgressBar(maxval=len(tests), widgets=widgets)
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
        print
        for test, trace in self.failures:
            if test.__module__ == '__main__':
                name = test.__name__
            else:
                name = '.'.join((test.__module__, test.__name__))
            print colorize('bold', name)
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
    """Collection of test functions.

    :param tests:
        Iterable of other :class:`Tests` instances to register with this one.

    """

    def __init__(self, tests=()):
        self._tests = []
        for collection in tests:
            self.register(collection)
        self._context = None

    def __iter__(self):
        return iter(self._tests)

    def __len__(self):
        return len(self._tests)

    def test(self, func):
        """Decorate a function as a test belonging to this collection."""
        @wraps(func)
        def wrapper():
            if self._context is None:
                func()
            else:
                with self._context() as context:
                    if len(inspect.getargspec(func)[0]) != 0:
                        if type(context) is tuple:  # type() is intentional
                            func(*context)
                        else:
                            func(context)
                    else:
                        func()
        self._tests.append(wrapper)
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
                    yield con
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
        tests defined in its collection, so it's less repetitive.

        Yielding :const:`None` or nothing passes no arguments to the test,
        yielding a single value other than a tuple passes that value as
        the sole argument to the test, yielding a tuple splats the tuple
        as the arguments to the test. If you want to yield a tuple as
        the sole argument, wrap it in a one-tuple or unsplat the args
        in the test.

        """
        func = contextmanager(func)
        self._context = func
        return func

    def register(self, tests):
        """Merge in another test collection."""
        self._tests.extend(tests)

    def test_suite(self):
        """Create a :class:`unittest.TestSuite` from this collection."""
        from unittest import TestSuite, FunctionTestCase
        suite = TestSuite()
        for test in self:
            suite.addTest(FunctionTestCase(test))
        return suite

    def run(self, formatter=FancyFormatter):
        """Run all tests in this collection.

        :param formatter:
            A class implementing :class:`AbstractFormatter` (not enforced).

        """
        failed = False
        if not isinstance(formatter, AbstractFormatter):
            formatter = formatter(self)
        for test in self:
            try:
                assert test() is not False, 'test returned False'
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


def test(meth):
    """Mark a method as a test, if defined in a class inheriting
    :class:`TestBase`.

    """
    meth.__test__ = True
    return meth


class TestBase(object):
    """Base for test classes. Decorate test methods with :func:`test`. Needs
    to be registered with a :class:`Tests` collection to be run. For setup
    and teardown, override :meth:`__context__` like a
    :func:`~contextlib.contextmanager` (without the decorator).

    ::

        class Math(TestBase):

            def __context__(self):
                self.two = 1 + 1
                yield
                del self.two

            @test
            def arithmetics(self):
                Assert(self.two) == 2

        suite = Tests([Math()])
        suite.run()

    """

    def __context__(self):
        yield

    def __iter__(self):
        ctx = contextmanager(self.__context__)
        for name in dir(self):
            attr = getattr(self, name)
            if getattr(attr, '__test__', False) and callable(attr):
                @wraps(attr)
                def wrapper():
                    with ctx():
                        attr()
                yield wrapper


class Loader(object):
    """Run tests with Attest via distribute::

        setup(
            test_loader='attest:Loader',
            test_suite='tests.collection',
        )

    Now, ``python setup.py -q test`` is equivalent to::

        from tests import collection
        collection.run()

    If you want to run the tests as a normal unittest suite,
    try :meth:`Tests.test_suite` instead::

        setup(
            test_suite='tests.collection.test_suite'
        )

    """

    def loadTestsFromNames(self, names, module=None):
        mod, collection = names[0].rsplit('.', 1)
        mod = __import__(mod, fromlist=[collection])
        collection = getattr(mod, collection)
        collection.run()
        raise SystemExit


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

    @property
    def __class__(self):
        return Assert(self.obj.__class__)

    def __eq__(self, obj):
        assert self.obj == obj, '%r != %r' % (self.obj, obj)
        return True

    def __ne__(self, obj):
        assert self.obj != obj, '%r == %r' % (self.obj, obj)
        return True

    def is_(self, obj):
        """The :keyword:`is` operator is not overridable, for good reasons
        (that would defeat its purpose), so you can use this method for
        asserting identity::

            Assert(True).is_(True)

        """
        assert self.obj is obj, '%r is not %r' % (self.obj, obj)
        return True

    def is_not(self, obj):
        """The negated form of :meth:`is_`, corresponding to the ``is not``
        operation::

            Assert([]).is_not([])

        """
        assert self.obj is not obj, '%r is %r' % (self.obj, obj)
        return True

    def __contains__(self, obj):
        assert obj in self.obj, '%r not in %r' % (obj, self.obj)
        return True

    def in_(self, obj):
        """Assert membership. While you can use the :keyword:`in` operator,
        its order is inconsistent with the rest of the operators and doesn't
        work with the ``not in`` operation.

        ::

            2 in Assert([1, 2, 3])
            Assert(2).in_([1, 2, 3])

        """
        assert self.obj in obj, '%r not in %r' % (self.obj, obj)
        return True

    def not_in(self, obj):
        """The negated form of :meth:`in_`, corresponding to the ``not in``
        operation::

            Assert(0).not_in([1, 2, 3])

        """
        assert self.obj not in obj, '%r in %r' % (self.obj, obj)
        return True

    def __lt__(self, obj):
        assert self.obj < obj, '%r >= %r' % (self.obj, obj)
        return True

    def __le__(self, obj):
        assert self.obj <= obj, '%r > %r' % (self.obj, obj)
        return True

    def __gt__(self, obj):
        assert self.obj > obj, '%r <= %r' % (self.obj, obj)
        return True

    def __ge__(self, obj):
        assert self.obj >= obj, '%r < %r' % (self.obj, obj)
        return True

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

    def __getitem__(self, key):
        return Assert(self.obj[key])

    def __getattr__(self, name):
        return Assert(getattr(self.obj, name))

    def __call__(self, *args, **kwargs):
        return Assert(self.obj(*args, **kwargs))

    def __repr__(self):
        return 'Assert(%r)' % self.obj
