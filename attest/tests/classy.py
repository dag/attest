from attest import TestBase, test, Assert, Tests, test_if

from .collections import TestReporter


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


suite = Tests()


@suite.test
def classbased_test_runs():
    """Tests().register(TestBase())"""

    instance = Classy()
    col = Tests([instance])

    Assert(len(col)) == 2
    Assert(list(col)[0]) == instance.fail

    result = TestReporter()
    col.run(result)

    Assert(len(result.succeeded)) == 1
    Assert(len(result.failed)) == 1

    Assert(result.failed[0].test) == instance.fail
    Assert(result.failed[0].exc_info[0]).is_(AssertionError)


@suite.test
def class_context():
    """TestBase().__context__"""

    instance = Contextual()
    col = Tests([instance])

    result = TestReporter()
    col.run(result)

    Assert(hasattr(instance, 'two')) == False
    Assert(len(result.failed)) == 0
    Assert(len(result.succeeded)) == 1


@suite.test
def decorative():
    """@Tests().register(TestBase)"""

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


@suite.test
def decorative_conditional():
    """@Tests().register_if(condition)(TestBase)"""

    col = Tests()

    class IncludedTest(TestBase):

        @test
        def foo(self):
            pass

        @test
        def bar(self):
            pass


    class ExcludedTest(TestBase):

        @test
        def spam(self):
            pass

        @test
        def eggs(self):
            pass

    col.register_if(True)(IncludedTest)
    col.register_if(False)(ExcludedTest)

    Assert(len(col)) == 2
    Assert(sorted(test.__name__ for test in col)) == ['bar', 'foo']


@suite.test
def conditional():
    """@test_if(condition)"""

    col = Tests()

    class TestClass(TestBase):
        @test
        def foo(self):
            pass

        @test_if(True)
        def bar(self):
            pass

        @test_if(False)
        def baz(self):
            assert False

    col.register(TestClass)

    result = TestReporter()
    col.run(result)
    Assert(len(result.failed)) == 0
    Assert(len(result.succeeded)) == 2
