from __future__ import with_statement

import sys

from attest import Tests, assert_hook, Assert, TestFailure
import attest


suite = Tests()


@suite.test
def capture():
    """capture_output()"""

    stdout, stderr = sys.stdout, sys.stderr

    with attest.capture_output() as (out, err):
        print 'Capture the flag!'
        print >>sys.stderr, 'Rapture the flag?'

    assert out == ['Capture the flag!']
    assert err == ['Rapture the flag?']

    assert sys.stdout is stdout
    assert sys.stderr is stderr


@suite.test
def disable_imports():
    with attest.disable_imports('sys', 'os'):
        with Assert.raises(ImportError):
            import sys

        with Assert.raises(ImportError):
            import os

    import sys
    import os

    with attest.disable_imports():
        import datetime
        assert datetime is sys.modules['datetime']


@suite.test
def raises():
    try:
        with attest.raises(RuntimeError):
            pass
    except AssertionError, e:
        assert type(e) is AssertionError
        assert str(e) == "didn't raise RuntimeError when expected"
    else:
        raise AssertionError

    # Groups of allowed exceptions
    try:
        with attest.raises(RuntimeError, ValueError):
            pass
    except AssertionError, e:
        assert type(e) is AssertionError
        assert str(e) == "didn't raise (RuntimeError, ValueError) when expected"
    else:
        raise AssertionError

    with attest.raises(RuntimeError, ValueError) as error:
        raise RuntimeError
    assert isinstance(error.exc, RuntimeError)

    with attest.raises(RuntimeError, ValueError) as error:
        raise ValueError('invaluable')
    assert isinstance(error.exc, ValueError) and str(error) == 'invaluable'

    with attest.raises(AssertionError):
        assert error.args == ('valuable',)
