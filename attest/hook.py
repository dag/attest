import importlib.machinery
import importlib.util
import inspect
import sys
import types
from pathlib import Path

from attest import ast, statistics
from attest.codegen import SourceGenerator, to_source

__all__ = ['COMPILES_AST',
           'ExpressionEvaluator',
           'TestFailure',
           'assert_hook',
           'AssertTransformer',
           'AssertImportHook',
          ]


try:
    compile(ast.parse('pass'), '<string>', 'exec')
except TypeError:
    COMPILES_AST = False
else:
    COMPILES_AST = True


class ExpressionEvaluator(SourceGenerator):
    """Evaluates ``expr`` in the context of ``globals`` and ``locals``,
    expanding the values of variables and the results of binary operations, but
    keeping comparison and boolean operators.

    .. testsetup::

        from attest import ExpressionEvaluator

    >>> var = 1 + 2
    >>> value = ExpressionEvaluator('var == 5 - 3', globals(), locals())
    >>> value.late_visit()
    >>> repr(value)
    '(3 == 2)'
    >>> bool(value)
    False

    .. versionadded:: 0.5

    """

    def __init__(self, expr, globals, locals):
        self.expr = expr
        # Putting locals in globals for closures
        self.globals = dict(globals)
        self.locals = locals
        self.globals.update(self.locals)

        self.result = []
        self.node = ast.parse(self.expr).body[0].value

    # Trigger visit after init because we don't want to
    # evaluate twice in case of a successful assert
    def late_visit(self):
        self.visit(self.node)

    def __repr__(self):
        return ''.join(self.result)

    def __str__(self):
        return '\n'.join((self.expr, repr(self)))

    def __bool__(self):
        return bool(eval(self.expr, self.globals, self.locals))

    def eval(self, node):
        return eval(to_source(node), self.globals, self.locals)

    def write(self, s):
        self.result.append(str(s))

    def visit_Name(self, node):
        value = self.eval(node)
        if getattr(value, '__name__', None):
            self.write(value.__name__)
        else:
            self.write(repr(value))

    def generic_visit(self, node):
        self.write(repr(self.eval(node)))

    visit_BinOp = visit_Subscript = generic_visit
    visit_ListComp = visit_GeneratorExp = generic_visit
    visit_SetComp = visit_DictComp = generic_visit
    visit_Call = visit_Attribute = generic_visit


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
    """Like ``assert``, but using :class:`ExpressionEvaluator`. If
    you import this in test modules and the :class:`AssertImportHook` is
    installed (which it is automatically the first time you import from
    :mod:`attest`), ``assert`` statements are rewritten as a call to
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
        # Visit only if assertion fails
        value.late_visit()
        raise TestFailure(value, msg)


# Build AST nodes more easily
def _build(node, **kwargs):
    node = node()
    for key, value in kwargs.items():
        setattr(node, key, value)
    return node


class AssertTransformer(ast.NodeTransformer):
    """Parses `source` with :mod:`_ast` and transforms `assert`
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
        module = types.ModuleType(name)
        module.__file__ = self.filename
        if newpath:
            module.__path__ = newpath
        sys.modules[name] = module
        exec(self.code, vars(module))
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
        if node.msg is not None:
            msg = node.msg
        else:
            msg = _build(ast.Constant, value='')
        args = [_build(ast.Constant, value=to_source(node.test)),
                msg,
                _build(ast.Call,
                    func=_build(ast.Name, id='globals', ctx=ast.Load()),
                    args=[], keywords=[]),
                _build(ast.Call,
                    func=_build(ast.Name, id='locals', ctx=ast.Load()),
                    args=[], keywords=[])
               ]
        return ast.copy_location(
            _build(ast.Expr, value=_build(ast.Call,
                   func=_build(ast.Name, id='assert_hook', ctx=ast.Load()),
                   args=args, keywords=[])), node)


class AssertImportHookEnabledDescriptor:

    def __get__(self, instance, owner):
        return any(isinstance(ih, owner) for ih in sys.meta_path)


class AssertImportHook:
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

    def __enter__(self):
        sys.meta_path.insert(0, self)

    def __exit__(self, exc_type, exc_value, traceback):
        sys.meta_path.remove(self)

    def find_module(self, name, path=None):
        try:
            # Use PathFinder directly to avoid triggering meta_path hooks again
            spec = importlib.machinery.PathFinder.find_spec(name, path)
            if spec is None:
                return None
            self._cache[name] = spec
        except (ImportError, ModuleNotFoundError, ValueError):
            return None
        return self

    def load_module(self, name):
        if name in sys.modules:
            return sys.modules[name]

        spec = self._cache.get(name)
        if spec is None:
            raise ImportError(f'cannot find module {name}')

        source, filename, newpath = self.get_source(name)

        if source is None:
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            return module

        transformer = AssertTransformer(source, filename)

        if not transformer.should_rewrite:
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            return module

        try:
            return transformer.make_module(name, newpath)
        except Exception as err:
            raise ImportError(f'cannot import {name}: {err}') from err

    def get_source(self, name):
        spec = self._cache.get(name)
        if spec is None:
            raise ImportError(name)

        code = filename = newpath = None

        if spec.submodule_search_locations is not None:
            # It's a package
            filename_path = None
            if spec.origin:
                filename_path = Path(spec.origin)
            else:
                first_location = next(iter(spec.submodule_search_locations), None)
                if first_location is not None:
                    filename_path = Path(first_location) / '__init__.py'
            newpath = spec.submodule_search_locations
            if filename_path is not None:
                filename = str(filename_path)
                try:
                    code = filename_path.read_text()
                except (OSError, TypeError, ValueError):  # Missing or invalid file paths
                    pass
        elif isinstance(spec.loader, importlib.machinery.SourceFileLoader):
            # It's a regular Python source file
            if spec.origin:
                filename_path = Path(spec.origin)
                filename = str(filename_path)
                try:
                    code = filename_path.read_text()
                except OSError:  # Missing or unreadable files
                    pass
        elif isinstance(spec.loader, importlib.machinery.SourcelessFileLoader):
            # It's a compiled Python file (.pyc)
            if spec.origin and spec.origin.endswith('.pyc'):
                filename_path = Path(spec.origin).with_suffix('.py')
                filename = str(filename_path)
                try:
                    code = filename_path.read_text()
                except OSError:  # Missing source file
                    pass

        return code, filename, newpath
