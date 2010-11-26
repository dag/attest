# coding:utf-8
from __future__ import with_statement

import threading
import sys
import traceback
from functools import wraps
import inspect
from contextlib import contextmanager, nested

try:
    from abc import ABCMeta, abstractmethod
except ImportError:
    ABCMeta = type
    abstractmethod = lambda x: x

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


REPORTERS = {}


statistics = threading.local()
statistics.assertions = 0


class AbstractReporter(object):
    """Optional base for reporters, serves as documentation and improves
    errors for incomplete reporters.

    :param tests: The list of test functions we will be running.

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def begin(self, tests):
        """Called with the list of tests when a test run has begun."""
        raise NotImplementedError

    @abstractmethod
    def success(self, test, stdout, stderr):
        """When a test succeeds, this method is called with the test
        function and the captured stdout and stderr output as lists of
        lines.

        """
        raise NotImplementedError

    @abstractmethod
    def failure(self, test, error, traceback, stdout, stderr):
        """When a test fails, this method is called with the test
        function, the exception instance that was raised, a cleaned up
        traceback string and the captured stdout and stderr output as lists
        of lines.

        """
        raise NotImplementedError

    @abstractmethod
    def finished(self):
        """Called when all tests have run."""
        raise NotImplementedError


class PlainReporter(AbstractReporter):
    """Plain text ASCII output for humans."""

    def begin(self, tests):
        self.total = len(tests)
        self.failures = []

    def success(self, test, stdout, stderr):
        sys.stdout.write('.')
        sys.stdout.flush()

    def failure(self, test, error, traceback, stdout, stderr):
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

REPORTERS['plain'] = PlainReporter


class FancyReporter(AbstractReporter):
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

    def success(self, test, stdout, stderr):
        self.counter += 1
        self.progress.update(self.counter)

    def failure(self, test, error, traceback, stdout, stderr):
        self.counter += 1
        self.progress.update(self.counter)
        self.failures.append((test, traceback, stdout, stderr))

    def finished(self):
        from pygments.console import colorize
        from pygments import highlight
        from pygments.lexers import PythonTracebackLexer
        from pygments.formatters import Terminal256Formatter

        self.progress.finish()
        print
        for test, trace, out, err in self.failures:
            if test.__module__ == '__main__':
                name = test.__name__
            else:
                name = '.'.join((test.__module__, test.__name__))
            print colorize('bold', name)
            if test.__doc__:
                print inspect.getdoc(test)
            print '─' * 80
            if out:
                print colorize('faint', '\n'.join(out))
            if err:
                print colorize('darkred', '\n'.join(err))
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

REPORTERS['fancy'] = FancyReporter


def auto_reporter(style=None):
    """Select a reporter based on the target output.

    This is the default reporter.

    :param style: Passed to :class:`FancyReporter` if it is used.
    :rtype:
        :class:`FancyReporter` if output is a terminal otherwise a
        :class:`PlainReporter`.

    """
    if sys.stdout.isatty():
        if style is None:
            return FancyReporter()
        return FancyReporter(style)
    return PlainReporter()

REPORTERS['auto'] = auto_reporter


class XmlReporter(AbstractReporter):
    """Report the result of a testrun in an XML format. Not compatible with
    JUnit or XUnit.

    """

    def __init__(self):
        self.escape = __import__('cgi').escape

    def begin(self, tests):
        print '<?xml version="1.0" encoding="UTF-8"?>'
        print '<testreport tests="%d">' % len(tests)

    def success(self, test, stdout, stderr):
        name = '.'.join((test.__module__, test.__name__))
        print '  <pass name="%s"/>' % name

    def failure(self, test, error, traceback, stdout, stderr):
        name = '.'.join((test.__module__, test.__name__))
        if isinstance(error, AssertionError):
            tag = 'fail'
        else:
            tag = 'error'
        print '  <%s name="%s" type="%s">' % (tag, name,
                                              error.__class__.__name__)
        print self.escape('\n'.join(' ' * 4 + line
                                    for line in
                                    traceback.splitlines()), quote=True)
        print '  </%s>' % tag

    def finished(self):
        print '</testreport>'

REPORTERS['xml'] = XmlReporter


def get_reporter_by_name(name, default='auto'):
    """Get an :class:`AbstractReporter` by name, falling back on a default.

    Available reporters:

    * ``'fancy'`` — :class:`FancyReporter`
    * ``'plain'`` — :class:`PlainReporter`
    * ``'xml'`` — :class:`XmlReporter`
    * ``'auto'`` — :func:`auto_reporter`

    :param name: One of the above strings.
    :param default:
        The fallback reporter if no reporter has the supplied name,
        defaulting to ``'auto'``.
    :raises KeyError:
        If neither the name or the default is a valid name of a reporter.
    :rtype: Callable returning an instance of an :class:`AbstractReporter`.

    """
    return REPORTERS.get(name, REPORTERS[default])


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


class Tests(object):
    """Collection of test functions.

    :param tests:
        Iterable of other test collections to register with this one.

    """

    def __init__(self, tests=()):
        self._tests = []
        for collection in tests:
            self.register(collection)
        self._contexts = []

    def __iter__(self):
        return iter(self._tests)

    def __len__(self):
        return len(self._tests)

    def test(self, func):
        """Decorate a function as a test belonging to this collection."""
        @wraps(func)
        def wrapper():
            with nested(*[ctx() for ctx in self._contexts]) as context:
                if len(inspect.getargspec(func)[0]) != 0:
                    args = []
                    for arg in context:
                        if type(arg) is tuple:  # type() is intentional
                            args.extend(arg)
                        else:
                            args.append(arg)
                    func(*args)
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

        You can have more than one context, which will be run in order
        using :func:`contextlib.nested`, and their yields will be passed in
        order to the test functions.

        .. versionadded:: 0.2 Nested contexts.

        """
        func = contextmanager(func)
        self._contexts.append(func)
        return func

    def register(self, tests):
        """Merge in another test collection.

        :param tests:
            * A class, which is then instantiated and return allowing it to be
              used as a decorator for :class:`TestBase` classes.
            * A string, representing the import path to an iterable yielding
              tests, in the form of ``'package.module.object'``.
            * Otherwise any iterable object is assumed to yield tests.

        Any of these can be passed in a list to the :class:`Tests`
        constructor.

        .. versionadded:: 0.2
           Refer to collections by import path as a string

        """
        if inspect.isclass(tests):
            self._tests.extend(tests())
            return tests
        elif isinstance(tests, basestring):
            package, collection = tests.rsplit('.', 1)
            module = package.rsplit('.', 1)[1]
            tests = getattr(__import__(package, fromlist=[module]), collection)
        self._tests.extend(tests)

    def test_suite(self):
        """Create a :class:`unittest.TestSuite` from this collection."""
        from unittest import TestSuite, FunctionTestCase
        suite = TestSuite()
        for test in self:
            suite.addTest(FunctionTestCase(test))
        return suite

    def run(self, reporter=auto_reporter):
        """Run all tests in this collection.

        :param reporter:
            An instance of :class:`AbstractReporter` or a callable
            returning something implementing that API (not enforced).

        """
        if not isinstance(reporter, AbstractReporter):
            reporter = reporter()
        reporter.begin(self._tests)
        for test in self:
            try:
                with capture_output() as (out, err):
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
                reporter.failure(test, e, '\n'.join(clean), out, err)
            else:
                reporter.success(test, out, err)
        reporter.finished()

    def main(self, argv=sys.argv):
        """Interface to :meth:`run` with command-line options.

        ``-h``, ``--help``
            Show a help message

        ``-r NAME``, ``--reporter NAME``
            Select reporter by name with :func:`get_reporter_by_name`

        Remaining arguments are passed to the reporter.

        .. versionadded:: 0.2

        """
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option('-r', '--reporter', metavar='NAME',
                          help='select reporter by name')
        options, args = parser.parse_args()
        reporter = get_reporter_by_name(options.reporter)(*args)
        self.run(reporter)


def test(meth):
    """Mark a :class:`TestBase` method as a test and wrap it to run in the
    :meth:`TestBase.__context__` of the subclass.

    """
    @wraps(meth)
    def wrapper(self):
        with contextmanager(self.__context__)():
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

    #: The wrapped object
    obj = None

    def __init__(self, obj=None):
        self.obj = obj

    @property
    def __class__(self):
        return Assert(self.obj.__class__)

    def __str__(self):
        """Wrapped proxy to the wrapped object's *__str__*, can be used for
        testing the string adaption of the object::

            Assert(1).__str__() == '1'

        .. warning:: :func:`str` on :class:`Assert` objects does not work.

        """
        return Assert(self.obj.__str__())

    def __getattr__(self, name):
        """Proxy all attributes to the wrapped object, wrapping the
        result.

        """
        return Assert(getattr(self.obj, name))

    def __call__(self, *args, **kwargs):
        """Allow calling of wrapped callables, wrapping the return value.
        Useful for testing methods on a wrapped object via attribute
        proxying::

            Assert('Hello').upper() == 'HELLO'

        """
        return Assert(self.obj(*args, **kwargs))

    def __getitem__(self, key):
        """Access an item on the wrapped object and return the result
        wrapped as well.

        ::

            Assert([1, 2, 3])[1] == 2

        """
        return Assert(self.obj[key])

    def __eq__(self, obj):
        """Test for equality with ``==``."""
        return assert_(self.obj == obj, '%r != %r' % (self.obj, obj))

    def __ne__(self, obj):
        """Test for inequality with ``!=``."""
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
        """Test for membership with :keyword:`in`."""
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
        """Test for lesserness with ``<``."""
        return assert_(self.obj < obj, '%r >= %r' % (self.obj, obj))

    def __le__(self, obj):
        """Test for lesserness or equality with ``<=``."""
        return assert_(self.obj <= obj, '%r > %r' % (self.obj, obj))

    def __gt__(self, obj):
        """Test for greaterness with ``>``."""
        return assert_(self.obj > obj, '%r <= %r' % (self.obj, obj))

    def __ge__(self, obj):
        """Test for greaterness or equality with ``>=``."""
        return assert_(self.obj >= obj, '%r < %r' % (self.obj, obj))

    def __nonzero__(self):
        """Test for truthiness in boolean context."""
        return assert_(self.obj, 'not %r' % self.obj)

    @staticmethod
    @contextmanager
    def raises(*exceptions):
        """Context manager that fails if a particular exception is not
        raised. Yields the caught exception wrapped in :class:`Assert`::

            with Assert.raises(IOError) as error:
                open('/etc/passwd', 'w')

            error.errno == 13

        :param exceptions: Expected exception classes.

        """
        statistics.assertions += 1
        proxy = Assert()
        try:
            yield proxy
        except exceptions, error:
            proxy.obj = error
        else:
            if len(exceptions) > 1:
                errors = '(' + ', '.join(e.__name__ for e in exceptions) + ')'
            else:
                errors = exceptions[0].__name__
            raise AssertionError("didn't raise %s" % errors)

    @staticmethod
    @contextmanager
    def not_raising(exception):
        """Context manager that fails if a particular exception is raised.
        A raised exception consitutes a failure anyway and this is mainly
        used for testing Attest itself.

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

    def __repr__(self):
        """Not proxied to the wrapped object. To test that do something
        like::

            Assert(repr(obj)) == 'expectation'

        """
        return 'Assert(%r)' % self.obj
