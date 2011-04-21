from __future__ import with_statement
from attest import Tests, assert_hook, utils, disable_imports

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
