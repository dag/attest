from attest import Tests, assert_hook
from attest.hook import ExpressionEvaluator


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
        ev = repr(ExpressionEvaluator(expr, globals(), locals()))
        assert ev == result
        assert bool(ev) is True
