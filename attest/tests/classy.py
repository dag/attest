from attest import TestBase, test, Tests, test_if, assert_hook, TestFailure

from .collectors import TestReporter


class Classy(TestBase):

    @test
    def fail(self):
        assert 1 == 2

    @test
    def succeed(self):
        assert 1 == 1


class Contextual(TestBase):

    def __context__(self):
        self.two = 1 + 1
        yield
        del self.two

    @test
    def succeed(self):
        assert self.two == 2


suite = Tests()


@suite.test
def classbased_test_runs():
    """Tests().register(TestBase())"""

    instance = Classy()
    col = Tests([instance])

    assert len(col) == 2
    assert list(col)[0] == instance.fail

    result = TestReporter()
    col.run(result)

    assert len(result.succeeded) == 1
    assert len(result.failed) == 1

    assert result.failed[0].test == instance.fail
    assert result.failed[0].exc_info[0] is TestFailure


@suite.test
def class_context():
    """TestBase().__context__"""

    instance = Contextual()
    col = Tests([instance])

    result = TestReporter()
    col.run(result)

    assert hasattr(instance, 'two') == False
    assert len(result.failed) == 0
    assert len(result.succeeded) == 1


@suite.test
def decorative():
    """@Tests().register(TestBase)"""

    col = Tests()
    assert len(col) == 0

    class DecoratedTest(TestBase):

        @test
        def noop(self):
            pass

        @test
        def nothing(self):
            pass

    DecoratedTest = col.register(DecoratedTest)

    assert issubclass(DecoratedTest, TestBase) == True
    assert len(col) == 2


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

    assert len(col) == 2
    assert sorted(test.__name__ for test in col) == ['bar', 'foo']


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
    assert len(result.failed) == 0
    assert len(result.succeeded) == 2
