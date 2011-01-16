"""

    Test tests for testing testing.

"""

from attest import Tests, assert_


metatests = Tests()

@metatests.test
def passing():
    pass

@metatests.test
def failing():
    value = 1 + 1
    assert_(value == 3, 'not (2 == 3)')
