# coding:utf-8
from __future__ import with_statement

import inspect
from contextlib import contextmanager, nested
import sys
from functools import wraps

from .contexts import capture_output
from .reporters import (auto_reporter, get_reporter_by_name,
                        get_all_reporters, AbstractReporter, TestResult)


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
                argc = len(inspect.getargspec(func)[0])
                args = []
                for arg in context:
                    if type(arg) is tuple:  # type() is intentional
                        args.extend(arg)
                    else:
                        args.append(arg)
                func(*args[:argc])
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
                assert con is not None

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
                    assert con is not None

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

        .. versionchanged:: 0.5
            Tests will gets as many arguments as they ask for.

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
            An instance of :class:`~attest.reporters.AbstractReporter` or a
            callable returning something implementing that API (not
            enforced).

        """
        if not isinstance(reporter, AbstractReporter):
            reporter = reporter()
        reporter.begin(self._tests)
        for test in self:
            result = TestResult()
            result.test = test
            try:
                with capture_output() as (out, err):
                    if test() is False:
                        raise AssertionError('test() is False')
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
            Select reporter by name with
            :func:`~attest.reporters.get_reporter_by_name`

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
                assert self.two == 2

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
