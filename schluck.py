# coding:utf-8
import traceback
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

class TextFormatter(AbstractFormatter):
    """A simple text formatter."""
    width = 80
    separator = 80 * "="

    def __init__(self, tests):
        self.counter = 0
        self.failures = []

    def success(self, test):
        self.counter += 1

    def failure(self, test, error, traceback):
        self.failures.append((test, traceback))

    def finished(self):
        import inspect
        for test, trace in self.failures:
            print self.separator
            print '.'.join((test.__module__, test.__name__))
            if test.__doc__:
                print inspect.getdoc(test)
            print self.separator
            print trace
            print 

        failed = len(self.failures)
        print 'Failures: %s/%s' % (failed, self.counter)
        

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
        import inspect
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

    def test(self, func):
        """Decorate a function as a test belonging to this collection."""
        self.tests.append(func)
        return func

    def register(self, tests):
        """Merge in another test collection."""
        self.tests.extend(tests.tests)

    def run(self, formatter=None):
        """Run all tests in this collection.

        :param formatter:
            An object implementing :class:`AbstractFormatter` (not enforced).
            Defaults to :class:`FancyFormatter`.

        """
        failed = False
        if formatter is None:
            formatter = FancyFormatter(self.tests)
        for test in self.tests:
            try:
                test()
            except Exception, e:
                failed = True
                lines = traceback.format_exc().splitlines()
                for index, line in enumerate(lines):
                    if __file__[0:-1] in line:
                        del lines[index]
                        del lines[index]
                formatter.failure(test, e, '\n'.join(lines))
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

    """

    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, obj):
        assert self.obj == obj, '%s != %s' % (self.obj, obj)

    def __ne__(self, obj):
        assert self.obj != obj, '%s == %s' % (self.obj, obj)

    def is_(self, obj):
        """The :keyword:`is` operator is not overridable, for good reasons
        (that would defeat its purpose), so you can use this method for
        asserting identity::

            Assert(True).is_(True)

        """
        assert self.obj is obj, '%s is not %s' % (self.obj, obj)

    def is_not(self, obj):
        """The negated form of :meth:`is_`, corresponding to the ``is not``
        operation::

            Assert([]).is_not([])

        """
        assert self.obj is not obj, '%s is %s' % (self.obj, obj)

    def __contains__(self, obj):
        assert obj in self.obj, '%s not in %s' % (obj, self.obj)

    def in_(self, obj):
        """Assert membership. While you can use the :keyword:`in` operator,
        its order is inconsistent with the rest of the operators and doesn't
        work with the ``not in`` operation.

        ::

            2 in Assert([1, 2, 3])
            Assert(2).in_([1, 2, 3])

        """
        assert self.obj in obj, '%s not in %s' % (self.obj, obj)

    def not_in(self, obj):
        """The negated form of :meth:`in_`, corresponding to the ``not in``
        operation::

            Assert(0).not_in([1, 2, 3])

        """
        assert self.obj not in obj, '%s in %s' % (self.obj, obj)

    def __lt__(self, obj):
        assert self.obj < obj, '%s >= %s' % (self.obj, obj)

    def __le__(self, obj):
        assert self.obj <= obj, '%s > %s' % (self.obj, obj)

    def __gt__(self, obj):
        assert self.obj > obj, '%s <= %s' % (self.obj, obj)

    def __ge__(self, obj):
        assert self.obj >= obj, '%s < %s' % (self.obj, obj)

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
