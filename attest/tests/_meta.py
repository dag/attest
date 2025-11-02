"""

    Test tests for testing testing.

"""
import sys
from attest import Tests, assert_hook


suite = Tests()

@suite.test
def passing():
    pass

@suite.test
def failing():
    print('stdout')
    print('stderr', file=sys.stderr)
    value = 1 + 1
    assert value == 3
