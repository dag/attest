from __future__ import absolute_import

from schluck import TestBase, test, Assert, Tests

from .collections import TestFormatter


class Classy(TestBase):

    @test
    def fail(self):
        Assert(1) == 2


class Contextual(TestBase):

    def __context__(self):
        self.two = 1 + 1
        yield
        del self.two

    @test
    def succeed(self):
        Assert(self.two) == 2


classy = Tests()

@classy.test
def classbased_test_runs():
    
    instance = Classy()
    col = Tests([instance])

    Assert(len(col)) == 1
    Assert(list(col)[0].__name__) == instance.fail.__name__

    result = TestFormatter(col)
    with Assert.raises(SystemExit):
        col.run(result)

    Assert(len(result.failed)) == 1
    Assert(len(result.succeeded)) == 0

    result.failed[0].test.__name__ == instance.fail.__name__
    result.failed[0].error.__class__.is_(AssertionError)

@classy.test
def class_context():

    instance = Contextual()
    col = Tests([instance])

    result = TestFormatter(col)
    try:
        col.run(result)
    except SystemExit:
        raise AssertionError('Contextual test failed')

    Assert(hasattr(instance, 'two')) == False
