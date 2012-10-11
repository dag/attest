from __future__ import with_statement
import inspect
from contextlib import contextmanager
from attest import Tests, assert_hook, utils, disable_imports, raises
import attest
from attest.utils import import_dotted_name

suite = Tests()


@suite.test
def terminal_size():
    size = utils.get_terminal_size()
    assert type(size) is tuple
    assert len(size) == 2
    assert type(size[0]) is int
    assert type(size[1]) is int

    with disable_imports('fcntl', 'termios'):
        size = utils.get_terminal_size()
        assert size == (80, 24)
        size = utils.get_terminal_size((1, 2))
        assert size == (1, 2)


@suite.test
def string_importing():
    assert import_dotted_name('attest') is attest
    assert import_dotted_name('attest.tests') is attest.tests
    assert import_dotted_name('attest.utils') is utils
    assert import_dotted_name('attest.utils:import_dotted_name') \
           is import_dotted_name
    assert import_dotted_name('attest.utils.import_dotted_name') \
           is import_dotted_name


    with raises(AttributeError):
        import_dotted_name('attest._nil')

    with raises(ImportError):
        with disable_imports('attest'):
            import_dotted_name('attest')


@suite.test
def iter_mods():
    core = ['attest'] + ['attest.' + mod for mod in
            '''ast codegen collectors contexts deprecated hook __main__
               reporters run statistics utils pygments'''.split()]
    tests = ['attest.tests'] + ['attest.tests.' + mod for mod in
            '''asserts classy collectors contexts hook _meta reporters utils
               dummy dummy.foo'''.split()]

    found = list(utils.deep_iter_modules('attest'))
    expected = core + tests
    assert set(expected) == set(found)
    assert len(expected) == len(found)

    found = list(utils.deep_iter_modules('attest.tests'))
    expected = tests
    assert set(expected) == set(found)
    assert len(expected) == len(found)

    found = list(utils.deep_iter_modules('attest.ast'))
    assert found == ['attest.ast']

    with raises(AttributeError):
        list(utils.deep_iter_modules('attest._nil'))

    with disable_imports('attest'):
        with raises(ImportError):
            list(utils.deep_iter_modules('attest'))


@suite.test
def get_members_recursively():
    deepfunc = lambda x: getattr(x, '__name__', '').startswith('deep_')
    found = list(utils.deep_get_members('attest', deepfunc))
    expected = [utils.deep_get_members, utils.deep_iter_modules]
    assert found == expected

    getters = lambda x: getattr(x, '__name__', '').startswith('get')
    found = set(utils.deep_get_members('inspect', getters))
    expected = set(v for (k, v) in inspect.getmembers(inspect, getters))
    assert found == expected


@suite.test
def reporter_options():
    opts = utils.parse_options([
        'style = dark',
        'verbose=yes',
        'quiet=no',
        'switch=on',
        'bigbutton=off',
        'bool=true',
        'lie=false',
        'num=3',
        'list=1,2,3',
        'pair=foo:bar',
        'dict=foo:bar,abc:123',
        'notopt',
        'empty=',
        'void=none',
        'hyphens-are-ok=true',
    ])

    assert opts == dict(
        style='dark',
        verbose=True,
        quiet=False,
        switch=True,
        bigbutton=False,
        bool=True,
        lie=False,
        num=3,
        list=(1, 2, 3),
        pair=dict(foo='bar'),
        dict=dict(foo='bar', abc=123),
        empty=None,
        void=None,
        hyphens_are_ok=True,
    )


@suite.test
def nesting_contexts():

    signals = []

    @contextmanager
    def one():
        signals.append('inner one')
        try:
            yield 'one'
        finally:
            signals.append('outer one')

    @contextmanager
    def two():
        signals.append('inner two')
        try:
            yield 'two'
        finally:
            signals.append('outer two')

    ctx = utils.nested([one, two])
    assert not signals

    with raises(ZeroDivisionError):
        with ctx as args:
            assert signals == ['inner one', 'inner two']
            assert args == ['one', 'two']
            1/0
    assert signals == ['inner one', 'inner two', 'outer two', 'outer one']

    args = None
    signals = []

    @contextmanager
    def one():
        signals.append('inner one')
        try:
            yield 'one'
        finally:
            signals.append('outer one')

    @contextmanager
    def two():
        signals.append('inner two')
        1/0
        try:
            yield 'two'
        finally:
            signals.append('outer two')

    ctx = utils.nested([one, two])
    assert not signals

    with raises(ZeroDivisionError):
        with ctx as args:
            pass

    assert signals == ['inner one', 'inner two', 'outer one']
    assert args is None


@suite.test
def counter():
    counter = utils.counter()
    assert counter.increment("a") == 1
    assert counter == {"a": 1}


@suite.test
def nested():
    try:
        with utils.nested([]):
            assert 1 == 0, "message"

    except AssertionError, e:
        print e.args
        assert e.args == ("message", )
