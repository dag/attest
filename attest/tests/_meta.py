"""

    Test tests for testing testing.

"""

from attest import Tests


metatests = Tests()

@metatests.test
def passing():
    pass

@metatests.test
def failing():
    assert False
