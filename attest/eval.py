from . import ast
from .codegen import to_source, SourceGenerator
import inspect


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
        return eval(self.expr, self.globals, self.locals)

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
