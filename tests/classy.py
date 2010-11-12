from __future__ import absolute_import

from schluck import TestBase, test, Assert, Tests

from .collections import TestFormatter


class Classy(TestBase):

    @test
    def fail(self):
        Assert(1) == 2


classy = Tests()

@classy.test
def classbased_test_runs():
    
    instance = Classy()
    col = Tests([instance])

    Assert(len(col)) == 1
    Assert(list(col)[0]) == instance.fail

    result = TestFormatter(col)
    with Assert.raises(SystemExit):
        col.run(result)

    Assert(len(result.failed)) == 1
    Assert(len(result.succeeded)) == 0

    result.failed[0].test == instance.fail
    result.failed[0].error.__class__.is_(AssertionError)
