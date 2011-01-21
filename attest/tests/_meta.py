"""

    Test tests for testing testing.

"""
from attest import Tests


suite = Tests()

@suite.test
def passing():
    pass

@suite.test
def failing():
    value = 1 + 1
    assert value == 3
