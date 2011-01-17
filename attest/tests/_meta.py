"""

    Test tests for testing testing.

"""
from attest import Tests, assert_hook


metatests = Tests()

@metatests.test
def passing():
    pass

@metatests.test
def failing():
    value = 1 + 1
    assert value == 3
