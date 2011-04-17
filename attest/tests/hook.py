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

    # FIXME Referencing a local inside a list comprehension fails on Python
    # 3.1 for some reason, with a NameError saying *global* name not
    # defined. Passing locals as globals works.

    """
    >>> eval("[f(v) for f in (str,float)]", globals(), dict(v=2))
    Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "<string>", line 1, in <module>
    File "<string>", line 1, in <listcomp>
    NameError: global name 'v' is not defined
    >>> eval("[f(v) for f in (str,float)]", dict(v=2), globals())
    ['2', 2.0]
    """

    for expr, result in samples.iteritems():
        ev = repr(ExpressionEvaluator(expr, globals(), locals()))
        assert ev == result
        assert bool(ev) is True
