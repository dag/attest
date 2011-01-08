# coding:utf-8
from __future__ import with_statement

import threading
import sys
import traceback
from functools import wraps
import inspect
from contextlib import contextmanager, nested
from pkg_resources import iter_entry_points

try:
    from abc import ABCMeta, abstractmethod
except ImportError:
    ABCMeta = type
    abstractmethod = lambda x: x

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO



statistics = threading.local()
statistics.assertions = 0


class TestResult(object):
    """Container for result data from running a test.

    .. versionadded:: 0.4

    """

    #: The test callable.
    test = None

    #: The exception instance, if the test failed.
    error = None

    #: The :func:`~sys.exc_info` of the exception, if the test failed.
    exc_info = None

    #: A list of lines the test printed on the standard output.
    stdout = None

    #: A list of lines the test printed on the standard error.
    stderr = None

    @property
    def test_name(self):
        """A representative name for the test, similar to its import path.

        """
        parts = []
        if self.test.__module__ != '__main__':
            parts.append(self.test.__module__)
        if hasattr(self.test, 'im_class'):
            parts.append(self.test.im_class.__name__)
        parts.append(self.test.__name__)
        return '.'.join(parts)

    @property
    def traceback(self):
        """The traceback for the exception, if the test failed, cleaned up.

        """
        lines = traceback.format_exception(*self.exc_info)
        lines = ''.join(lines).splitlines()
        clean = lines[:1]
        stack = iter(lines[1:-1])  # stack traces are in the middle
        # loop two lines at a time
        for first, second in zip(stack, stack):
            # only keep if this file is not the source of the trace
            if __file__[:-1] not in first:
                clean.extend((first, second))
        clean.append(lines[-1])
        return '\n'.join(clean)


class AbstractReporter(object):
    """Optional base for reporters, serves as documentation and improves
    errors for incomplete reporters.

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def begin(self, tests):
        """Called when a test run has begun.

        :param tests: The list of test functions we will be running.

        """
        raise NotImplementedError

    @abstractmethod
    def success(self, result):
        """Called when a test succeeds.

        :param result: Result data for the succeeding test.
        :type result: :class:`TestResult`

        .. versionchanged:: 0.4
            Parameters changed to `result`.

        """
        raise NotImplementedError

    @abstractmethod
    def failure(self, result):
        """Called when a test fails.

        :param result: Result data for the failing test.
        :type result: :class:`TestResult`

        .. versionchanged:: 0.4
            Parameters changed to `result`.

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

    def success(self, result):
        sys.stdout.write('.')
        sys.stdout.flush()

    def failure(self, result):
        if isinstance(result.error, AssertionError):
            sys.stdout.write('F')
        else:
            sys.stdout.write('E')
        sys.stdout.flush()
        self.failures.append(result)

    def finished(self):
        print
        print
        for result in self.failures:
            print result.test_name
            if result.test.__doc__:
                print inspect.getdoc(result.test)
            print '-' * 80
            print result.traceback
            print

        print 'Failures: %s/%s (%s assertions)' % (len(self.failures),
                                                   self.total,
                                                   statistics.assertions)

        if self.failures:
            raise SystemExit(1)


class FancyReporter(AbstractReporter):
    """Heavily uses ANSI escape codes for fancy output to 256-color
    terminals. Progress of running the tests is indicated by a progressbar
    and failures are shown with syntax highlighted tracebacks.

    :param style:
        `Pygments`_ style for tracebacks, defaults to ``'bw'`` because it
        looks good on most terminals.

    .. _Pygments: http://pygments.org/

    """

    def __init__(self, style='bw'):
        self.style = style
        import progressbar
        import pygments

    def begin(self, tests):
        from progressbar import ProgressBar, Percentage, \
                                Bar, ETA, SimpleProgress
        widgets = [SimpleProgress(), ' [', ETA(), Bar(), Percentage(), ']']
        self.counter = 0
        self.progress = ProgressBar(maxval=len(tests), widgets=widgets)
        self.progress.start()
        self.failures = []

    def success(self, result):
        self.counter += 1
        self.progress.update(self.counter)

    def failure(self, result):
        self.counter += 1
        self.progress.update(self.counter)
        self.failures.append(result)

    def finished(self):
        from pygments.console import colorize
        from pygments import highlight
        from pygments.lexers import PythonTracebackLexer
        from pygments.formatters import Terminal256Formatter

        self.progress.finish()
        print
        for result in self.failures:
            print colorize('bold', result.test_name)
            if result.test.__doc__:
                print inspect.getdoc(result.test)
            print '─' * 80
            if result.stdout:
                print colorize('faint', '\n'.join(result.stdout))
            if result.stderr:
                print colorize('darkred', '\n'.join(result.stderr))
            print highlight(result.traceback, PythonTracebackLexer(),
                            Terminal256Formatter(style=self.style))

        if self.failures:
            failed = colorize('red', str(len(self.failures)))
        else:
            failed = len(self.failures)
        print 'Failures: %s/%s (%s assertions)' % (failed, self.counter,
                                                   statistics.assertions)

        if self.failures:
            raise SystemExit(1)


def auto_reporter(style=None):
    """Select a reporter based on the target output and installed
    dependencies.

    This is the default reporter.

    :param style: Passed to :class:`FancyReporter` if it is used.
    :rtype:
        :class:`FancyReporter` if output is a terminal and the progressbar
        and pygments packages are installed, otherwise a
        :class:`PlainReporter`.

    """
    if sys.stdout.isatty():
        try:
            if style is None:
                return FancyReporter()
            return FancyReporter(style)
        except ImportError:
            pass
    return PlainReporter()


class XmlReporter(AbstractReporter):
    """Report the result of a testrun in an XML format. Not compatible with
    JUnit or XUnit.

    """

    def __init__(self):
        self.escape = __import__('cgi').escape

    def begin(self, tests):
        print '<?xml version="1.0" encoding="UTF-8"?>'
        print '<testreport tests="%d">' % len(tests)

    def success(self, result):
        print '  <pass name="%s"/>' % result.test_name

    def failure(self, result):
        if isinstance(result.error, AssertionError):
            tag = 'fail'
        else:
            tag = 'error'
        print '  <%s name="%s" type="%s">' % (tag, result.test_name,
                                              result.exc_info[0].__name__)
        print self.escape('\n'.join(' ' * 4 + line
                                    for line in
                                    result.traceback.splitlines()),
                          quote=True)
        print '  </%s>' % tag

    def finished(self):
        print '</testreport>'


def get_reporter_by_name(name, default='auto'):
    """Get an :class:`AbstractReporter` by name, falling back on a default.

    Reporters are registered via setuptools entry points, in the
    ``'attest.reporters'`` group. A third-party reporter can thus register
    itself using this in its :file:`setup.py`::

        setup(
            entry_points = {
                'attest.reporters': [
                    'name = import.path.to:callable'
                ]
            }
        )

    Names for the built in reporters:

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

    .. versionchanged:: 0.4
        Reporters are registered via setuptools entry points.

    """
    reporter = None
    if name is not None:
        reporter = list(iter_entry_points('attest.reporters', name))
    if not reporter:
        reporter = list(iter_entry_points('attest.reporters', default))
    if not reporter:
        raise KeyError
    return reporter[0].load()


def get_all_reporters():
    """Iterable yielding the names of all registered reporters.

    >>> from attest import get_all_reporters
    >>> list(get_all_reporters())
    ['xml', 'plain', 'fancy', 'auto']

    .. versionadded:: 0.4

    """
    for ep in iter_entry_points('attest.reporters'):
        yield ep.name


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


class Tests(object):
    """Collection of test functions.

    :param tests:
        Iterable of other test collections to register with this one.
    :param contexts:
        Iterable of callables that take no arguments and return a context
        manager.

    """

    def __init__(self, tests=(), contexts=None):
        self._tests = []
        for collection in tests:
            self.register(collection)
        self._contexts = []
        if contexts is not None:
            self._contexts.extend(contexts)

    def __iter__(self):
        return iter(self._tests)

    def __len__(self):
        return len(self._tests)

    def test_if(self, condition):
        """Returns :meth:`test` if the `condition` is ``True``.

        .. versionadded:: 0.4

        """
        if condition:
            return self.test
        return lambda x: x

    def test(self, func):
        """Decorate a function as a test belonging to this collection."""
        @wraps(func)
        def wrapper():
            with nested(*[ctx() for ctx in self._contexts]) as context:
                context = [c for c in context if c is not None]
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

            @contextmanager
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

    def register_if(self, condition):
        """Returns :meth:`register` if the `condition` is ``True``.

        .. versionadded:: 0.4

        """
        if condition:
            return self.register
        return lambda x: x

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
            module, collection = str(tests).rsplit('.', 1)
            module = __import__(module, fromlist=[collection])
            tests = getattr(module, collection)
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
            result = TestResult()
            result.test = test
            try:
                with capture_output() as (out, err):
                    assert test() is not False, 'test returned False'
            except BaseException, e:
                if isinstance(e, KeyboardInterrupt):
                    break
                result.error = e
                result.stdout, result.stderr = out, err
                result.exc_info = sys.exc_info()
                reporter.failure(result)
            else:
                result.stdout, result.stderr = out, err
                reporter.success(result)
        reporter.finished()

    def main(self, argv=sys.argv):
        """Interface to :meth:`run` with command-line options.

        ``-h``, ``--help``
            Show a help message

        ``-r NAME``, ``--reporter NAME``
            Select reporter by name with :func:`get_reporter_by_name`

        ``-l``, ``--list-reporters``
            List the names of all installed reporters


        Remaining arguments are passed to the reporter.

        .. versionadded:: 0.2

        .. versionchanged:: 0.4 ``--list-reporters`` was added.

        """
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option('-r', '--reporter', metavar='NAME',
                          help='select reporter by name')
        parser.add_option('-l', '--list-reporters', action='store_true',
                          help='list available reporters')
        options, args = parser.parse_args()
        if options.list_reporters:
            for reporter in get_all_reporters():
                print reporter
        else:
            reporter = get_reporter_by_name(options.reporter)(*args)
            self.run(reporter)


def test_if(condition):
    """Returns :func:`test` if the `condition` is ``True``.

    .. versionadded:: 0.4

    """
    if condition:
        return test
    return lambda x: x


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
        if isinstance(obj, Assert):
            self.obj = obj.obj
        else:
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

        .. versionchanged:: 0.3
            Checks the wrapped object for :class:`Assert` instances.

        """
        if isinstance(obj, Assert):
            obj = obj.obj
        return assert_(self.obj is obj, '%r is not %r' % (self.obj, obj))

    def is_not(self, obj):
        """The negated form of :meth:`is_`, corresponding to the ``is not``
        operation::

            Assert([]).is_not([])

        .. versionchanged:: 0.3
            Checks the wrapped object for :class:`Assert` instances.

        """
        if isinstance(obj, Assert):
            obj = obj.obj
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
        return bool(assert_(self.obj, 'not %r' % self.obj))

    @staticmethod
    @contextmanager
    def raises(*exceptions):
        """Context manager that fails if *none* of the `exceptions` are
        raised. Yields the captured exception as an :term:`assertive
        object`.

        ::

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

    @staticmethod
    def isinstance(obj, classinfo):
        """Test that an object is an instance of a class or a :func:`tuple`
        of classes. Corresponds to :func:`.isinstance`.

        .. versionadded:: 0.4

        """
        if isinstance(obj, Assert):
            obj = obj.obj
        return assert_(isinstance(obj, classinfo),
                       'not isinstance(%r, %s)' % (obj, _repr(classinfo)))

    @staticmethod
    def not_isinstance(obj, classinfo):
        """Negated version of :meth:`isinstance`.

        .. versionadded:: 0.4

        """
        if isinstance(obj, Assert):
            obj = obj.obj
        return assert_(not isinstance(obj, classinfo),
                       'isinstance(%r, %s)' % (obj, _repr(classinfo)))

    @staticmethod
    def issubclass(obj, cls):
        """Test that `obj` is a subclass of `cls` or a subclass of a class
        inside `cls`. Corresponds to :func:`.issubclass`.

        .. versionadded:: 0.4

        """
        if isinstance(obj, Assert):
            obj = obj.obj
        return assert_(issubclass(obj, cls),
                       'not issubclass(%s, %s)' % (_repr(obj), _repr(cls)))

    @staticmethod
    def not_issubclass(obj, cls):
        """Negated version of :meth:`issubclass`.

        .. versionadded:: 0.4

        """
        if isinstance(obj, Assert):
            obj = obj.obj
        return assert_(not issubclass(obj, cls),
                       'issubclass(%s, %s)' % (_repr(obj), _repr(cls)))

    @property
    def json(self):
        """Parse the wrapped object as JSON. Requires Python 2.6 or the
        simplejson package.

        .. versionadded:: 0.4

        """
        try:
            import simplejson as json
        except ImportError:
            import json
        return Assert(json.loads(self.obj))

    def css(self, selector):
        """Parse the wrapped object as :abbr:`HTML
        (HyperText Markup Language)` and return an :term:`assertive
        <assertive object>` list of elements matching the :abbr:`CSS
        (Cascading Style Sheets)` `selector`.  Requires lxml 2.0 or newer.

        .. note::

            Not tested on Python 2.5 and PyPy due to difficulties
            installing lxml for these implementations.

        .. versionadded:: 0.4

        """
        from lxml import html
        return Assert(html.fromstring(self.obj).cssselect(selector))

    def xpath(self, path):
        """Parse the wrapped object as :abbr:`XML
        (eXtensible Markup Language)` and return an :term:`assertive
        <assertive object>` list of elements matching the :abbr:`XPath
        (XML Path Language)` *path*.  Requires lxml 2.0 or newer.

        .. note::

            Not tested on Python 2.5 and PyPy due to difficulties
            installing lxml for these implementations.

        .. versionadded:: 0.4

        """
        from lxml import etree
        return Assert(etree.fromstring(self.obj).xpath(path))

    def passed_to(self, func, *args, **kwargs):
        """Pass the unwrapped object to a function and return its result
        as an :term:`assertive object`.

        These are identical::

            Assert(len([1, 2, 3])) == 3
            Assert([1, 2, 3]).passed_to(len) == 3

        Mainly useful with Assert objects that comes from the outside, e.g.
        yielded from a context, from methods like :meth:`css` etc.

        .. versionadded:: 0.4

        """
        return Assert(func(self.obj, *args, **kwargs))

    def attr(self, name):
        """Safely get an attribute from the wrapped object.

        .. versionadded:: 0.4

        """
        return Assert(getattr(self.obj, name))

    def __repr__(self):
        """Not proxied to the wrapped object. To test that do something
        like::

            Assert(repr(obj)) == 'expectation'

        """
        return 'Assert(%r)' % self.obj


def _repr(obj):
    """Internal :func:`repr` that tries to be more close to original
    code.

    """
    if inspect.isclass(obj):
        return obj.__name__
    elif type(obj) is tuple:
        return '(%s)' % ', '.join(map(_repr, obj))
    return repr(obj)
