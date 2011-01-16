from . import ast
from .codegen import to_source, SourceGenerator
from . import statistics
import inspect
import imp
import os
import sys


class ExpressionEvaluator(SourceGenerator):

    def __init__(self, expr, globals, locals):
        self.expr = expr
        self.globals, self.locals = globals, locals
        self.result = []
        node = ast.parse(self.expr).body[0].value
        self.visit(node)

    def __repr__(self):
        return ''.join(self.result)

    def __nonzero__(self):
        return bool(eval(self.expr, self.globals, self.locals))

    def eval(self, node):
        return eval(to_source(node), self.globals, self.locals)

    def write(self, s):
        self.result.append(s)

    def visit_Name(self, node):
        value = self.eval(node)
        if hasattr(value, '__name__'):
            self.write(value.__name__)
        else:
            self.write(repr(value))

    def generic_visit(self, node):
        self.write(repr(self.eval(node)))

    visit_BinOp = visit_Subscript = generic_visit


def evalexpr(expr, globals=None, locals=None):
    """Expands names and computations in an expression string, but retains
    function calls, type literals and comparative/boolean operations.

    >>> value = 1 + 1
    >>> evalexpr('value == int("2") and value < 5 - 2')
    ((2 == int('2')) and (2 < 3))

    """
    if globals is None:
        globals = inspect.stack()[1][0].f_globals
    if locals is None:
        locals = inspect.stack()[1][0].f_locals
    return ExpressionEvaluator(expr, globals, locals)


def assert_hook(expr, globals=None, locals=None):
    statistics.assertions += 1
    if globals is None:
        globals = inspect.stack()[1][0].f_globals
    if locals is None:
        locals = inspect.stack()[1][0].f_locals
    evaluated = evalexpr(expr, globals, locals)
    if not evaluated:
        raise AssertionError(evaluated)


def build(node, **kwargs):
    node = node()
    for key, value in kwargs.iteritems():
        setattr(node, key, value)
    return node


class AssertTransformer(ast.NodeTransformer):

    def __init__(self, source, filename=''):
        self.filename = filename
        node = ast.parse(source, filename)
        self.node = self.visit(node)
        ast.fix_missing_locations(self.node)

    @property
    def code(self):
        return compile(self.node, self.filename, 'exec')

    def visit_Assert(self, node):
        return ast.copy_location(
            build(ast.Expr, value=build(ast.Call,
                  func=build(ast.Name, id='assert_hook', ctx=ast.Load()),
                  args=[build(ast.Str, s=to_source(node.test))],
                  keywords=[], starargs=None, kwargs=None)), node)


class AssertImportHook(object):

    def __init__(self):
        self._cache = {}

    def find_module(self, name, path=None):
        lastname = name.rsplit('.', 1)[-1]
        try:
            self._cache[name] = imp.find_module(lastname, path), path
        except ImportError:
            return
        return self

    def load_module(self, name):
        if name in sys.modules:
            return sys.modules[name]

        source, filename, newpath = self.get_source(name)
        (fd, fn, info), path = self._cache[name]

        if source is None:
            return imp.load_module(name, fd, fn, info)

        if 'from attest import assert_hook' not in source.splitlines():
            return imp.load_module(name, open(filename), fn, info)

        try:
            module = imp.new_module(name)
            module.__file__ = filename
            if newpath:
                module.__path__ = newpath
            code = AssertTransformer(source, filename).code
            sys.modules[name] = module
            exec code in vars(module)
            return module

        except Exception, err:
            raise ImportError('cannot import %s: %s' % (name, err))

    def get_source(self, name):
        try:
            (fd, fn, info), path = self._cache[name]
        except KeyError:
            raise ImportError(name)

        code = filename = newpath = None
        if info[2] == imp.PY_SOURCE:
            filename = fn
            with fd:
                code = fd.read()
        elif info[2] == imp.PY_COMPILED:
            filename = fn[:-1]
            with open(filename, 'U') as f:
                code = f.read()
        elif info[2] == imp.PKG_DIRECTORY:
            filename = os.path.join(fn, '__init__.py')
            newpath = [fn]
            with open(filename, 'U') as f:
                code = f.read()

        return code, filename, newpath
