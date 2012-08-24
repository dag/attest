# coding:utf-8
import traceback
import sys
import os
from os import path
import inspect
from pkg_resources import iter_entry_points

try:
    from abc import ABCMeta, abstractmethod
except ImportError:
    ABCMeta = type
    abstractmethod = lambda x: x

from . import statistics
from .hook import (ExpressionEvaluator, TestFailure, COMPILES_AST,
                   AssertImportHook)


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
    def raw_traceback(self):
        """Like :func:`traceback.extract_tb` with uninteresting entries
        removed.

        .. versionadded:: 0.5

        """
        tb = traceback.extract_tb(self.exc_info[2])
        if not COMPILES_AST and AssertImportHook.enabled:
            newtb = []
            for filename, lineno, funcname, text in tb:
                newtb.append((filename, 0, funcname, None))
            tb = newtb
        clean = []
        thisfile = path.abspath(path.dirname(__file__))
        for item in tb:
            failfile = path.abspath(path.dirname(item[0]))
            if failfile != thisfile:
                clean.append(item)
        return clean

    @property
    def traceback(self):
        """The traceback for the exception, if the test failed, cleaned up.

        """
        clean = self.raw_traceback
        lines = ['Traceback (most recent call last):\n']
        lines += traceback.format_list(clean)
        msg = str(self.error)
        lines += traceback.format_exception_only(self.exc_info[0], msg)
        return ''.join(lines)[:-1]

    @property
    def assertion(self):
        if isinstance(self.error, TestFailure):
            expressions = str(self.error.value)
            return '\n'.join('assert %s' % expr
                             for expr in expressions.splitlines())


def _test_loader_factory(reporter):
    class Loader(object):
        def loadTestsFromNames(self, names, module=None):
            from .collectors import Tests
            Tests(names).run(reporter)
            raise SystemExit
    return Loader()


class AbstractReporter(object):
    """Optional base for reporters, serves as documentation and improves
    errors for incomplete reporters.

    """

    __metaclass__ = ABCMeta

    @classmethod
    def test_loader(cls):
        """Creates a basic unittest test loader using this reporter. This
        can be used to run tests via distribute, for example::

            setup(
                test_loader='attest:FancyReporter.test_loader',
                test_suite='tests.collection',
            )

        Now, ``python setup.py -q test`` is equivalent to::

            from attest import FancyReporter
            from tests import collection
            collection.run(FancyReporter)

        If you want to run the tests as a normal unittest suite,
        try :meth:`~attest.collectors.Tests.test_suite` instead::

            setup(
                test_suite='tests.collection.test_suite'
            )

        .. versionadded:: 0.5

        """
        return _test_loader_factory(cls)

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
            if result.stdout:
                print '->', '\n'.join(result.stdout)
            if result.stderr:
                print 'E:', '\n'.join(result.stderr)
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
        `Pygments`_ style for tracebacks. If :const:`None`, uses
        :envvar:`ATTEST_PYGMENTS_STYLE` falling back on ``'bw'`` because it
        looks good on most terminals.

    .. _Pygments: http://pygments.org/

    """

    def __init__(self, style=None):
        if style is None:
            self.style = os.environ.get('ATTEST_PYGMENTS_STYLE', 'bw')
        else:
            self.style = style
        import progressbar
        import pygments

    def begin(self, tests):
        from progressbar import ProgressBar, Percentage, ETA, SimpleProgress
        widgets = ['[', Percentage(), '] ', SimpleProgress(), ' ', ETA()]
        self.counter = 0
        self.progress = ProgressBar(maxval=len(tests), widgets=widgets,
                                    fd=sys.stderr)
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
            print colorize('faint', '─' * 80)
            for line in result.stdout:
                print colorize('bold', '→'),
                print line
            for line in result.stderr:
                print colorize('red', '→'),
                print line

            formatter = Terminal256Formatter(style=self.style)
            encoding = self._detect_code_encoding(result.raw_traceback[-1][0])
            print highlight(result.traceback.decode(encoding),
                            PythonTracebackLexer(),
                            formatter).encode(encoding)

            if result.assertion is not None:
                print highlight(result.assertion, PythonLexer(), formatter)

        if self.failures:
            failed = colorize('red', str(len(self.failures)))
        else:
            failed = len(self.failures)
        print 'Failures: %s/%s (%s assertions)' % (failed, self.counter,
                                                   statistics.assertions)

        if self.failures:
            raise SystemExit(1)

    def _detect_code_encoding(self, filename):
        """Detects code encoding from the magic encoding comment.

        """
        import re
        comment_pattern = re.compile(r'\s*#?')
        hint_pattern = re.compile(r'\s*#.*?coding(?::|\s*=)\s*([^\s]+)')
        with open(filename) as pyfile:
            for line in pyfile.xreadlines():
                if not comment_pattern.match(line):
                    break
                match = hint_pattern.match(line)
                if match is not None:
                    return match.group(1)
        return 'ascii'


def auto_reporter(style=None):
    """Select a reporter based on the target output and installed
    dependencies.

    This is the default reporter.

    :param style: Passed to :class:`FancyReporter` if it is used.
    :rtype:
        :class:`FancyReporter` if output is a terminal and the progressbar
        and pygments packages are installed, otherwise a
        :class:`PlainReporter`.

    .. versionchanged:: 0.5
        A `test_loader` function attribute similar to
        :meth:`AbstractReporter.test_loader`.

    """
    if sys.stdout.isatty():
        try:
            if style is None:
                return FancyReporter()
            return FancyReporter(style)
        except ImportError:
            pass
    return PlainReporter()

auto_reporter.test_loader = lambda: _test_loader_factory(auto_reporter)


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


class QuickFixReporter(AbstractReporter):
    """Report failures in a format that's understood by Vim's quickfix
    feature.

    Write a Makefile that runs your tests with this reporter and
    then from Vim you can do ``:mak``. If there's failures, Vim will jump
    to the first one by opening the offending file and positioning the
    cursor at the relevant line; you can jump between failures with ``:cn``
    and ``:cp``. For more information try `:help quickfix
    <http://vimdoc.sourceforge.net/htmldoc/quickfix.html>`_.

    Example Makefile (remember to indent with tabs not spaces)::

        test:
            @python runtests.py -rquickfix

    .. versionadded:: 0.5

    """

    failed = False

    def begin(self, tests):
        pass

    def success(self, result):
        pass

    def failure(self, result):
        self.failed = True
        fn, lineno = result.raw_traceback[-1][:2]
        type, msg = result.exc_info[0].__name__, str(result.exc_info[1])
        if msg:
            msg = ': ' + msg
        print "%s:%s: %s%s" % (fn, lineno, type, msg)

    def finished(self):
        if self.failed:
            raise SystemExit(1)


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
    * ``'quickfix'`` — :class:`QuickFixReporter`
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
    return reporter[0].load(require=False)


def get_all_reporters():
    """Iterable yielding the names of all registered reporters.

    >>> from attest import get_all_reporters
    >>> list(get_all_reporters())
    ['xml', 'plain', 'quickfix', 'fancy', 'auto']

    .. versionadded:: 0.4

    """
    for ep in iter_entry_points('attest.reporters'):
        yield ep.name
