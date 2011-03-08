from __future__ import with_statement
from . import ast
from .codegen import to_source, SourceGenerator
from . import statistics
import inspect
import imp
import os
import sys


try:
    compile(ast.parse('pass'), '<string>', 'exec')
except TypeError:
    COMPILES_AST = False
else:
    COMPILES_AST = True


class ExpressionEvaluator(SourceGenerator):
    """Evaluates `expr` in the context of `globals` and `locals`, expanding
    the values of variables and the results of binary operations, but
    keeping comparison and boolean operators.

    >>> from attest import ExpressionEvaluator
    >>> var = 1 + 2
    >>> value = ExpressionEvaluator('var == 5 - 3', globals(), locals())
    >>> repr(value)
    '(3 == 2)'
    >>> bool(value)
    False

    .. versionadded:: 0.5

    """

    def __init__(self, expr, globals, locals):
        self.expr = expr
        self.globals, self.locals = globals, locals
        self.result = []
        node = ast.parse(self.expr).body[0].value
        self.visit(node)

    def __repr__(self):
        return ''.join(self.result)

    def __str__(self):
        return '\n'.join((self.expr, repr(self)))

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


class TestFailure(AssertionError):
    """Extended :exc:`AssertionError` used by the assert hook.

    :param value: The asserted expression evaluated with
        :class:`ExpressionEvaluator`.
    :param msg: Optional message passed to the assertion.

    .. versionadded:: 0.5

    """

    def __init__(self, value, msg=''):
        self.value = value
        AssertionError.__init__(self, msg)


def assert_hook(expr, msg='', globals=None, locals=None):
    """Like :keyword:`assert`, but using :class:`ExpressionEvaluator`. If
    you import this in test modules and the :class:`AssertImportHook` is
    installed (which it is automatically the first time you import from
    :mod:`attest`), :keyword:`assert` statements are rewritten as a call to
    this.

    The import must be a top-level *from* import, example::

        from attest import Tests, assert_hook

    .. versionadded:: 0.5

    """
    statistics.assertions += 1
    if globals is None:
        globals = inspect.stack()[1][0].f_globals
    if locals is None:
        locals = inspect.stack()[1][0].f_locals
    value = ExpressionEvaluator(expr, globals, locals)
    if not value:
        raise TestFailure(value, msg)


# Build AST nodes on 2.5 more easily
def _build(node, **kwargs):
    node = node()
    for key, value in kwargs.iteritems():
        setattr(node, key, value)
    return node


class AssertTransformer(ast.NodeTransformer):
    """Parses `source` with :mod:`_ast` and transforms :keyword:`assert`
    statements into calls to :func:`assert_hook`.

    .. warning::

        CPython 2.5 doesn't compile AST nodes and when that fails this
        transformer will generate source code from the AST instead. While
        Attest's own tests passes on CPython 2.5, there might be code that
        it currently would render back incorrectly, most likely resulting
        in a failure. Because Python's syntax is simple, this isn't very
        likely, but you might want to :meth:`~AssertImportHook.disable` the
        import hook if you test regularly on CPython 2.5.

        It also messes up the line numbers so they don't match the original
        source code, meaning tracebacks will point to the line numbers in
        the *generated* source and preview the code on that line in the
        *original* source. The improved error message with the import hook
        is often worth it however, and failures will still point to the
        right file and function.

    .. versionadded:: 0.5

    """

    def __init__(self, source, filename=''):
        self.source = source
        self.filename = filename

    @property
    def should_rewrite(self):
        """:const:`True` if the source imports :func:`assert_hook`."""
        return ('assert_hook' in self.source and
                any(s.module == 'attest' and
                    any(n.name == 'assert_hook' for n in s.names)
                    for s in ast.parse(self.source).body
                    if isinstance(s, ast.ImportFrom)))

    def make_module(self, name, newpath=None):
        """Compiles the transformed code into a module object which it also
        inserts in :data:`sys.modules`.

        :returns: The module object.

        """
        module = imp.new_module(name)
        module.__file__ = self.filename
        if newpath:
            module.__path__ = newpath
        exec self.code in vars(module)
        sys.modules[name] = module
        return module

    @property
    def node(self):
        """The transformed AST node."""
        node = ast.parse(self.source, self.filename)
        node = self.visit(node)
        ast.fix_missing_locations(node)
        return node

    @property
    def code(self):
        """The :attr:`node` compiled into a code object."""
        if COMPILES_AST:
            return compile(self.node, self.filename, 'exec')
        return compile(to_source(self.node), self.filename, 'exec')

    def visit_Assert(self, node):
        args=[_build(ast.Str, s=to_source(node.test))]
        if node.msg is not None:
            args.append(node.msg)
        return ast.copy_location(
            _build(ast.Expr, value=_build(ast.Call,
                   func=_build(ast.Name, id='assert_hook', ctx=ast.Load()),
                   args=args, keywords=[], starargs=None, kwargs=None)), node)


class AssertImportHookEnabledDescriptor(object):

    def __get__(self, instance, owner):
        return any(isinstance(ih, owner) for ih in sys.meta_path)


class AssertImportHook(object):
    """An :term:`importer` that transforms imported modules with
    :class:`AssertTransformer`.

    .. versionadded:: 0.5

    """

    #: Class property, :const:`True` if the hook is enabled.
    enabled = AssertImportHookEnabledDescriptor()

    @classmethod
    def enable(cls):
        """Enable the import hook."""
        cls.disable()
        sys.meta_path.insert(0, cls())

    @classmethod
    def disable(cls):
        """Disable the import hook."""
        sys.meta_path[:] = [ih for ih in sys.meta_path
                               if not isinstance(ih, cls)]

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

        transformer = AssertTransformer(source, filename)

        if not transformer.should_rewrite:
            fd, fn, info = imp.find_module(name.rsplit('.', 1)[-1], path)
            return imp.load_module(name, fd, fn, info)

        try:
            return transformer.make_module(name, newpath)
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
