from attest import Tests, assert_hook
from attest.hook import ExpressionEvaluator


suite = Tests()

@suite.test
def eval():
    value = 1 + 1
    valgen = (v for v in [value])

    samples = {
        'isinstance(value, int)': 'True',
        'value == int("2")': "(2 == 2)",
        'value.denominator': '1',
        'value == 5 - 3': '(2 == 2)',
        '{"value": value}': "{'value': 2}",
        '[valgen.next() for _ in [value]] == [v for v in [value]]':
            '([2] == [2])',
    }

    for expr, result in samples.iteritems():
        ev = repr(ExpressionEvaluator(expr, globals(), locals()))
        assert ev == result
        assert bool(ev) is True
