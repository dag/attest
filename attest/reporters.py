# coding:utf-8
from __future__ import absolute_import, with_statement

import inspect
import os
import sys
import traceback
import unittest
import _ast

from os            import path
from pkg_resources import iter_entry_points
from datetime      import datetime
try:
    from abc import ABCMeta, abstractmethod
except ImportError:
    ABCMeta = type
    abstractmethod = lambda x: x

from attest      import statistics, utils
from attest.hook import (ExpressionEvaluator,
                         TestFailure,
                         COMPILES_AST,
                         AssertImportHook)


# TODO: find some better test
ANSI_COLORS_SUPPORT = True
if sys.platform == 'win32':
    try:
        import colorama
    except ImportError:
        ANSI_COLORS_SUPPORT = False
    else:
        colorama.init()


__all__ = ['TestResult',
           'AbstractReporter',
           'PlainReporter',
           'FancyReporter',
           'auto_reporter',
           'XmlReporter',
           'XUnitReporter',
           'QuickFixReporter',
           'get_reporter_by_name',
           'get_all_reporters',
          ]


class TestResult(object):
    """Container for result data from running a test.

    .. versionadded:: 0.4

    """

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    full_tracebacks = False

    debugger = False

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

    def debug(self):
        if self.debugger:
            import pdb
            tb = self.exc_info[2]
            pdb.post_mortem(tb)

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
        if self.full_tracebacks:
            return tb
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

    @property
    def equality_diff(self):
        if not isinstance(self.error, TestFailure):
            return
        # Create a dummy test case to use its assert* methods
        case = unittest.FunctionTestCase(lambda: None)
        case.maxDiff = 2000
        # Type-specific methods are only available since Python 2.7
        if hasattr(case, '_type_equality_funcs'):
            node = self.error.value.node
            if (isinstance(node, _ast.Compare) and len(node.ops) == 1 and
                    isinstance(node.ops[0], _ast.Eq)):
                # The assertion is something like 'left == right'
                left = self.error.value.eval(node.left)
                right = self.error.value.eval(node.comparators[0])
                if type(left) is type(right):
                    asserter = case._type_equality_funcs.get(type(left))
                    if asserter is not None:
                        if isinstance(asserter, basestring):
                            asserter = getattr(case, asserter)
                        try:
                            asserter(left, right)
                        except AssertionError, exc:
                            return '%s\n' % exc.args[0]


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

        width, _ = utils.get_terminal_size()
        for result in self.failures:
            print result.test_name
            if result.test.__doc__:
                print inspect.getdoc(result.test)
            print '-' * width
            if result.stdout:
                print '->', '\n'.join(result.stdout)
            if result.stderr:
                print 'E:', '\n'.join(result.stderr)
            print result.traceback
            print
            result.debug()

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
        `Pygments`_ style for tracebacks.
    :param verbose:
        Report on tests regardless of failure.
    :param colorscheme:
        If `style` is *light* or *dark*, maps token names to color names.

    .. admonition:: Styles

        Available styles can be listed with ``pygmentize -L styles``. The
        special values ``'light'`` and ``'dark'`` (referring to the terminal's
        background) use the 16 system colors rather than assuming a 256-color
        terminal.

        Defaults to *light* or the environment variable
        :envvar:`ATTEST_PYGMENTS_STYLE`.

    .. versionchanged:: 0.6 Added the 16-color styles *light* and *dark*
        and the complementary `colorscheme` option

    .. _Pygments: http://pygments.org/

    """

    def __init__(self, style=None, verbose=False, colorscheme=None):
        import progressbar, pygments
        self.style = style
        self.verbose = verbose
        self.colorscheme = colorscheme
        self.total_time  = 0
        if style is None:
            self.style = os.environ.get('ATTEST_PYGMENTS_STYLE', 'light')

    def begin(self, tests):
        from progressbar import ProgressBar, Percentage, ETA, SimpleProgress
        widgets = ['[', Percentage(), '] ', SimpleProgress(), ' ', ETA()]
        self.counter = 0
        self.progress = ProgressBar(maxval=len(tests), widgets=widgets)
        if tests:
            self.progress.start()
        self.passes = []
        self.failures = []

    def success(self, result):
        self.counter += 1
        self.total_time += result.time
        self.progress.update(self.counter)
        self.passes.append(result)

    def failure(self, result):
        self.counter += 1
        self.total_time += result.time
        self.progress.update(self.counter)
        self.failures.append(result)

    def finished(self):
        from pygments.lexers import (PythonTracebackLexer, PythonLexer,
                                     DiffLexer)
        if ANSI_COLORS_SUPPORT:
            from pygments.console import colorize
            from pygments import highlight

            if self.style in ('light', 'dark'):
                from pygments.formatters import TerminalFormatter
                formatter = TerminalFormatter(bg=self.style)
                if self.colorscheme is not None:
                    from pygments.token import string_to_tokentype
                    for token, value in self.colorscheme.iteritems():
                        token = string_to_tokentype(token.capitalize())
                        formatter.colorscheme[token] = (value, value)
            else:
                from pygments.formatters import Terminal256Formatter
                formatter = Terminal256Formatter(style=self.style)
        else:
            # ANSI color codes seem not to be supported, make colorize()
            # and highlight() no-ops.
            formatter = None
            def colorize(_format, text):
                return text
            def highlight(text, _lexer, _formatter):
                return text

        if self.counter:
            self.progress.finish()
        print

        width, _ = utils.get_terminal_size()
        def show(result):
            print colorize('bold', result.test_name)
            if result.test.__doc__:
                print inspect.getdoc(result.test)
            print colorize('faint', '─' * width)
            for line in result.stdout:
                print colorize('bold', '→'),
                print line
            for line in result.stderr:
                print colorize('red', '→'),
                print line

        if self.verbose:
            for result in self.passes:
                if result.stdout or result.stderr:
                    show(result)
                    print

        for result in self.failures:
            show(result)

            # result.traceback seems to be in UTF-8 on my system (eg. for
            # literal unicode strings) but I guess this depends on the source
            # file encoding. Tell Pygments to guess: try UTF-8 and then latin1.
            # Without an `encoding` argument, Pygments just uses latin1.
            print highlight(result.traceback,
                            PythonTracebackLexer(encoding='guess'),
                            formatter)

            assertion = result.assertion
            if assertion is not None:
                print highlight(assertion,
                                PythonLexer(encoding='guess'),
                                formatter)

            equality_diff = result.equality_diff
            if equality_diff is not None:
                print highlight(equality_diff,
                                DiffLexer(encoding='guess'),
                                formatter)

            result.debug()

        if self.failures:
            failed = colorize('red', str(len(self.failures)))
        else:
            failed = len(self.failures)
        print 'Failures: %s/%s (%s assertions, %.3f seconds)' % (
            failed, self.counter, statistics.assertions, self.total_time)

        if self.failures:
            raise SystemExit(1)


def auto_reporter(**opts):
    """Select a reporter based on the target output and installed
    dependencies.

    This is the default reporter.

    :param opts: Passed to :class:`FancyReporter` if it is used.
    :rtype:
        :class:`FancyReporter` if output is a terminal and the progressbar
        and pygments packages are installed, otherwise a
        :class:`PlainReporter`.

    .. versionchanged:: 0.5
        A `test_loader` function attribute similar to
        :meth:`AbstractReporter.test_loader`.

    """
    if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
        try:
            return FancyReporter(**opts)
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


class XUnitReporter(AbstractReporter):
    """Report the result of a testrun in an XUnit XML format.
    """

    def __init__(self, file=None):
        self.file = file
        self.escape = __import__('cgi').escape
        self.reports = []
        self.errors = 0
        self.failures = 0
        self.successes = 0
        self.total_time = 0
        try:
            import socket
            self.hostname = socket.gethostname()
        except:
            self.hostname = 'unknown'
        self.timestamp = datetime.isoformat(datetime.today())

    def begin(self, tests):
        pass

    def success(self, result):
        self.successes += 1
        self.total_time += result.time
        self.reports.append(
            '<testcase classname="%s" name="%s" time="%f" />' % (
                result.test_name, result.test.__name__, result.time))
        if self.file:
            print result.test_name, "... ok"

    def failure(self, result):
        self.total_time += result.time
        if isinstance(result.error, AssertionError):
            tag = 'failure'
            self.failures += 1
        else:
            tag = 'error'
            self.errors += 1

        error = '<testcase classname="%s" name="%s" time="%f">\n' % (
            result.test_name, result.test.__name__, result.time)

        error += '<%s type="%s" message="%s"><![CDATA[\n' % (
            tag,
            result.exc_info[0].__name__,
            self.escape(repr(result.exc_info[1]), quote=True))
        error += self.escape(
            '\n'.join(line
                    for line in
                    result.traceback.splitlines()),
            quote=True)
        error += '\n]]>\n</%s>\n</testcase>' % tag
        self.reports.append(error)
        if self.file:
            print result.test_name, "... ", tag

    def finished(self):
        out = '<?xml version="1.0" encoding="UTF-8"?>\n'
        out += ('<testsuite name="attest" tests="%d" ' +
                   'errors="%d" failures="%d" ' +
                   'hostname="%s" timestamp="%s" time="%f">\n') % (
                (self.errors + self.failures + self.successes),
                self.errors,
                self.failures,
                self.hostname,
                self.timestamp,
                self.total_time)
        out += '<properties />\n'
        out += '\n'.join(self.reports)
        out += '\n</testsuite>\n'

        if not self.file:
            print out
        else:
            with open(self.file, "w") as f:
                f.write(out)

        if self.failures + self.errors:
            raise SystemExit(1)


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
    * ``'xunit'`` – :class:`XUnitReporter`
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

    .. testsetup::

        from attest import get_all_reporters

    >>> list(get_all_reporters())
    ['xml', 'plain', 'xunit', 'fancy', 'auto', 'quickfix']

    .. versionadded:: 0.4

    """
    for ep in iter_entry_points('attest.reporters'):
        yield ep.name
