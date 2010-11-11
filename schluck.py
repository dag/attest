import traceback
import sys
import inspect

from pygments import highlight
from pygments.lexers import PythonTracebackLexer
from pygments.formatters import Terminal256Formatter


class Tests(object):

    def __init__(self):
        self.tests = []

    def test(self, func):
        self.tests.append(func)
        return func

    def register(self, tests):
        self.tests.extend(tests)

    def run(self):
        failures = []
        for test in self.tests:
            try:
                test()
            except Exception as e:
                if isinstance(e, AssertionError):
                    sys.stdout.write('F')
                else:
                    sys.stdout.write('E')
                lines = traceback.format_exc().splitlines()
                for index, line in enumerate(lines):
                    if __file__[0:-1] in line:
                        del lines[index]
                        del lines[index]
                failures.append((test, '\n'.join(lines)))
            else:
                sys.stdout.write('.')
            sys.stdout.flush()
        print
        for failure, trace in failures:
            print '-' * 80
            print '.'.join((failure.__module__, failure.__name__))
            if failure.__doc__:
                print inspect.getdoc(failure)
            print '-' * 80
            print highlight(trace, PythonTracebackLexer(),
                            Terminal256Formatter())
        if failures:
            raise SystemExit(1)


class Assert(object):

    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, obj):
        assert self.obj == obj, '{0} != {1}'.format(self.obj, obj)

    def __ne__(self, obj):
        assert self.obj != obj, '{0} == {1}'.format(self.obj, obj)

    def is_(self, obj):
        assert self.obj is obj, '{0} is not {1}'.format(self.obj, obj)

    def is_not(self, obj):
        assert self.obj is not obj, '{0} is {1}'.format(self.obj, obj)

    def __contains__(self, obj):
        assert obj in self.obj, '{0} not in {1}'.format(obj, self.obj)

    def in_(self, obj):
        assert self.obj in obj, '{0} not in {1}'.format(self.obj, obj)

    def not_in(self, obj):
        assert self.obj not in obj, '{0} in {1}'.format(self.obj, obj)

    def __lt__(self, obj):
        assert self.obj < obj, '{0} >= {1}'.format(self.obj, obj)

    def __le__(self, obj):
        assert self.obj <= obj, '{0} > {1}'.format(self.obj, obj)

    def __gt__(self, obj):
        assert self.obj > obj, '{0} <= {1}'.format(self.obj, obj)

    def __ge__(self, obj):
        assert self.obj >= obj, '{0} < {1}'.format(self.obj, obj)
