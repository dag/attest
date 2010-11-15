# coding:utf-8
from __future__ import with_statement

import threading
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


FORMATTERS = {}


statistics = threading.local()
statistics.assertions = 0


class AbstractFormatter(object):
    """Optional base for formatters, serves as documentation and improves
    errors for incomplete formatters.

    :param tests: The list of test functions we will be running.

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def begin(self, tests):
        """Called with the list of tests when a test run has begun."""
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

    def begin(self, tests):
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

        print 'Failures: %s/%s (%s assertions)' % (len(self.failures),
                                                   self.total,
                                                   statistics.assertions)

        if self.failures:
            raise SystemExit(1)

FORMATTERS['plain'] = PlainFormatter


class FancyFormatter(AbstractFormatter):
    """Heavily uses ANSI escape codes for fancy output to 256-color
    terminals. Progress of running the tests is indicated by a progressbar
    and failures are shown with syntax highlighted tracebacks.

    """

    def __init__(self, style='bw'):
        self.style = style

    def begin(self, tests):
        from progressbar import ProgressBar, Percentage, \
                                Bar, ETA, SimpleProgress
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
            print '─' * 80
            print highlight(trace, PythonTracebackLexer(),
                            Terminal256Formatter(style=self.style))

        if self.failures:
            failed = colorize('red', str(len(self.failures)))
        else:
            failed = len(self.failures)
        print 'Failures: %s/%s (%s assertions)' % (failed, self.counter,
                                                   statistics.assertions)

        if self.failures:
            raise SystemExit(1)

FORMATTERS['fancy'] = FancyFormatter


def auto_formatter(style=None):
    """Select a formatter based on the target output.

    This is the default formatter.

    :param style: Passed to :class:`FancyFormatter` if it is used.
    :rtype: :class:`FancyFormatter` if output is a terminal otherwise
         a :class:`PlainFormatter`.

    """
    if sys.stdout.isatty():
        if style is None:
            return FancyFormatter()
        return FancyFormatter(style)
    return PlainFormatter()

FORMATTERS['auto'] = auto_formatter


def get_formatter_by_name(name, default='auto'):
    """Get an :class:`AbstractFormatter` by name, falling back on a default.

    Available formatters:

    * ``'fancy'`` — :class:`FancyFormatter`
    * ``'plain'`` — :class:`PlainFormatter`
    * ``'auto'`` — :func:`auto_formatter`

    :param name: One of the above strings.
    :param default:
        The fallback formatter if no formatter has the supplied name,
        defaulting to ``'auto'``.
    :raises KeyError:
        If neither the name or the default is a valid name of a formatter.
    :rtype: Callable returning an instance of an :class:`AbstractFormatter`.

    """
    return FORMATTERS.get(name, FORMATTERS[default])


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
        if inspect.isclass(tests):
            self._tests.extend(tests())
            return tests
        self._tests.extend(tests)

    def test_suite(self):
        """Create a :class:`unittest.TestSuite` from this collection."""
        from unittest import TestSuite, FunctionTestCase
        suite = TestSuite()
        for test in self:
            suite.addTest(FunctionTestCase(test))
        return suite

    def run(self, formatter=auto_formatter):
        """Run all tests in this collection.

        :param formatter:
            An instance of :class:`AbstractFormatter` or a callable
            returning something implementing that API (not enforced).

        """
        if not isinstance(formatter, AbstractFormatter):
            formatter = formatter()
        formatter.begin(self._tests)
        for test in self:
            try:
                assert test() is not False, 'test returned False'
            except BaseException, e:
                if isinstance(e, KeyboardInterrupt):
                    break
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


def test(meth):
    """Mark a :class:`TestBase` method as a test and wrap it to run in the
    :meth:`TestBase.__context__` of the subclass.

    """
    @wraps(meth)
    def wrapper(self):
        with self.__context__():
            meth(self)
    wrapper.__test__ = True
    return wrapper


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
        if not getattr(self, '_context_initiated', False):
            self.__context__ = contextmanager(self.__context__)
            self._context_initiated = True
        for name in dir(self):
            attr = getattr(self, name)
            if getattr(attr, '__test__', False) and callable(attr):
                yield attr


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


def assert_(expr, msg=None):
    """Like :keyword:`assert`, but counts the assertion."""
    statistics.assertions += 1
    assert expr, msg
    return expr


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

    def __init__(self, obj=None):
        self.obj = obj

    @property
    def __class__(self):
        return Assert(self.obj.__class__)

    def __eq__(self, obj):
        return assert_(self.obj == obj, '%r != %r' % (self.obj, obj))

    def __ne__(self, obj):
        return assert_(self.obj != obj, '%r == %r' % (self.obj, obj))

    def is_(self, obj):
        """The :keyword:`is` operator is not overridable, for good reasons
        (that would defeat its purpose), so you can use this method for
        asserting identity::

            Assert(True).is_(True)

        """
        return assert_(self.obj is obj, '%r is not %r' % (self.obj, obj))

    def is_not(self, obj):
        """The negated form of :meth:`is_`, corresponding to the ``is not``
        operation::

            Assert([]).is_not([])

        """
        return assert_(self.obj is not obj, '%r is %r' % (self.obj, obj))

    def __contains__(self, obj):
        return assert_(obj in self.obj, '%r not in %r' % (obj, self.obj))

    def in_(self, obj):
        """Assert membership. While you can use the :keyword:`in` operator,
        its order is inconsistent with the rest of the operators and doesn't
        work with the ``not in`` operation.

        ::

            2 in Assert([1, 2, 3])
            Assert(2).in_([1, 2, 3])

        """
        return assert_(self.obj in obj, '%r not in %r' % (self.obj, obj))

    def not_in(self, obj):
        """The negated form of :meth:`in_`, corresponding to the ``not in``
        operation::

            Assert(0).not_in([1, 2, 3])

        """
        return assert_(self.obj not in obj, '%r in %r' % (self.obj, obj))

    def __lt__(self, obj):
        return assert_(self.obj < obj, '%r >= %r' % (self.obj, obj))

    def __le__(self, obj):
        return assert_(self.obj <= obj, '%r > %r' % (self.obj, obj))

    def __gt__(self, obj):
        return assert_(self.obj > obj, '%r <= %r' % (self.obj, obj))

    def __ge__(self, obj):
        return assert_(self.obj >= obj, '%r < %r' % (self.obj, obj))

    def __nonzero__(self):
        return assert_(self.obj, 'not %r' % self.obj)

    @staticmethod
    @contextmanager
    def raises(exception):
        """Context manager that fails if a particular exception is not
        raised. Yields the caught exception wrapped in :class:`Assert`::

            with Assert.raises(IOError) as error:
                open('/etc/passwd', 'w')

            error.errno == 13

        :param exception: An exception class.

        """
        statistics.assertions += 1
        proxy = Assert()
        try:
            yield proxy
        except exception, error:
            proxy.obj = error
        else:
            error = exception.__name__
            raise AssertionError("didn't raise %s" % error)

    @staticmethod
    @contextmanager
    def not_raising(exception):
        """Context manager that fails if a particular exception is raised.
        A raised exception consitutes a failure in itself but this can be
        used for exceptions such as :exc:`SystemExit` and for improving
        the failure report.

        ::

            with Assert.not_raising(IOError):
                open('/etc/passwd', 'r')

        :param exception: An exception class.

        """
        statistics.assertions += 1
        try:
            yield
        except exception:
            raise AssertionError('raised %s' % exception.__name__)

    def __getitem__(self, key):
        return Assert(self.obj[key])

    def __getattr__(self, name):
        return Assert(getattr(self.obj, name))

    def __call__(self, *args, **kwargs):
        return Assert(self.obj(*args, **kwargs))

    def __str__(self):
        return Assert(self.obj.__str__())

    def __repr__(self):
        return 'Assert(%r)' % self.obj
