from __future__ import with_statement

import sys

from attest import Tests, assert_hook, Assert
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
