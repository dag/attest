# coding:utf-8
import traceback
import sys
from os import path
import inspect
from pkg_resources import iter_entry_points

try:
    from abc import ABCMeta, abstractmethod
except ImportError:
    ABCMeta = type
    abstractmethod = lambda x: x

from . import statistics
from .eval import ExpressionEvaluator


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
        tb = traceback.extract_tb(self.exc_info[2])
        clean = []
        for item in tb:
            if path.dirname(item[0]) != path.dirname(__file__):
                clean.append(item)
        lines = ['Traceback (most recent call last):\n']
        lines += traceback.format_list(clean)
        msg = str(self.error)
        if not msg and isinstance(self.error, AssertionError):
            msg = self.evaluated_assertion
        lines += traceback.format_exception_only(self.exc_info[0], msg)
        return ''.join(lines)[:-1]

    @property
    def evaluated_assertion(self):
        """The :keyword:`assert` statement with the values of variables
        shown.

        Given::

            value = 1 + 1
            assert value == 3

        This property will then be the string ``not (2 == 3)``.

        .. versionadded:: 0.5

        """
        tb = self.exc_info[2]
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        expr = traceback.extract_tb(tb)[0][3].partition('assert ')[2]
        return 'not %r' % ExpressionEvaluator(expr, frame.f_globals,
                                              frame.f_locals)


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
        from progressbar import ProgressBar, Percentage, ETA, SimpleProgress
        widgets = ['[', Percentage(), '] ', SimpleProgress(), ' ', ETA()]
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
        from pygments.lexers import PythonTracebackLexer, PythonLexer
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

            formatter = Terminal256Formatter(style=self.style)

            if not isinstance(result.error, AssertionError):
                print highlight(result.traceback,
                                PythonTracebackLexer(),
                                formatter)

            else:
                traceback = result.traceback.splitlines()
                error, msg = traceback[-1].split(': ', 1)
                tb = highlight('\n'.join(traceback[:-1] + [error + ':']),
                               PythonTracebackLexer(), formatter).strip()
                tb += ' '
                tb += highlight(msg, PythonLexer(), formatter)
                print tb

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
