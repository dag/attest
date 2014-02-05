import types

from attest import Tests, assert_hook
from attest.hook import AssertImportHook, ExpressionEvaluator


suite = Tests()


@suite.test
def eval():
    value = 1 + 1

    samples = {
        'isinstance(value, int)': 'True',
        'value == int("2")': "(2 == 2)",
        'type(value).__name__': "'int'",
        'value == 5 - 3': '(2 == 2)',
        '{"value": value}': "{'value': 2}",
        '[v for v in [value]]': '[2]',
    }

    for expr, result in samples.iteritems():
        expr = ExpressionEvaluator(expr, globals(), locals())
        expr.late_visit()
        ev = repr(expr)
        assert ev == result
        assert bool(ev) is True


@suite.test
def initpy_with_relative_import():
    # Ensure that packages with an __init__.py file that use both assert_hook
    # and relative imports are hooked properly.
    from . import dummy


@suite.test
def get_code():
    loader = AssertImportHook()
    loader.find_module('sys')
    assert loader.get_code('sys') is None
    loader.find_module('cStringIO')
    assert loader.get_code('cStringIO') is None
    loader.find_module('StringIO')
    assert isinstance(loader.get_code('StringIO'), types.CodeType)
