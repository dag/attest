from attest import TestBase, test, Assert, Tests

from tests.collections import TestReporter


class Classy(TestBase):

    @test
    def fail(self):
        Assert(1) == 2

    @test
    def succeed(self):
        Assert(1) == 1


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

    Assert(len(col)) == 2
    Assert(list(col)[0]) == instance.fail

    result = TestReporter()
    col.run(result)

    Assert(len(result.succeeded)) == 1
    Assert(len(result.failed)) == 1

    result.failed[0].test == instance.fail
    result.failed[0].error.__class__.is_(AssertionError)

@classy.test
def class_context():

    instance = Contextual()
    col = Tests([instance])

    result = TestReporter()
    col.run(result)

    Assert(hasattr(instance, 'two')) == False
    Assert(len(result.failed)) == 0
    Assert(len(result.succeeded)) == 1

@classy.test
def decorative():

    col = Tests()
    Assert(len(col)) == 0

    class DecoratedTest(TestBase):

        @test
        def noop(self):
            pass

        @test
        def nothing(self):
            pass

    DecoratedTest = col.register(DecoratedTest)

    Assert(issubclass(DecoratedTest, TestBase)) == True
    Assert(len(col)) == 2
