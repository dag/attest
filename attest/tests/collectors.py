from __future__ import with_statement
from attest import (AbstractReporter, Tests, TestBase, Assert, assert_hook,
                    test, TestFailure)
import unittest


class TestReporter(AbstractReporter):

    def begin(self, tests):
        self.succeeded = []
        self.failed = []

    def success(self, result):
        self.succeeded.append(result)

    def failure(self, result):
        self.failed.append(result)

    def finished(self):
        pass


suite = Tests()


@suite.test
def decorator():
    """@Tests().test"""

    col = Tests()

    @col.test
    def one(): pass

    @col.test
    def two(): pass

    assert len(col) == 2
    assert [func.__wrapped__ for func in col] == [one, two]


@suite.test
def context():
    """@Tests().context"""

    col = Tests(replace_tests=True)

    @col.test
    def test(calculated):
        assert calculated == 2

    @col.context
    def context():
        calculated = 1 + 1
        yield calculated

    @col.test
    def noctx():
        pass

    test()
    noctx()

    col2 = Tests()

    @col2.context
    def empty():
        yield

    @col2.test
    def test2():
        pass

    test2()

    col3 = Tests(replace_tests=True)

    @col3.context
    def multiple():
        yield 1, 2, 3

    @col3.test
    def test3(one, two, three):
        assert one == 1
        assert two == 2
        assert three == 3

    @col3.test
    def test3_2(one, two):
        assert one == 1
        assert two == 2

    test3()
    test3_2()

    col4 = Tests(replace_tests=True)

    @col4.context
    def nested():
        yield 1

    @col4.context
    def nested():
        yield

    @col4.context
    def nested():
        yield 2

    @col4.test
    def test4(one, two):
        assert one == 1
        assert two == 2

    test4()

    from contextlib import contextmanager

    @contextmanager
    def context5():
        yield 1

    col5 = Tests(contexts=[context5], replace_tests=True)

    @col5.test
    def test5(one):
        assert one == 1

    test5()


@suite.test
def run():
    """Tests().run"""

    col = Tests()

    @col.test
    def fail():
        assert 1 == 2

    @col.test
    def succeed():
        assert 1 == 1

    @col.test
    def exit():
        raise SystemExit

    result = TestReporter()
    with Assert.not_raising(SystemExit):
        col.run(result)

    assert len(result.failed) == 2
    assert len(result.succeeded) == 1

    assert result.failed[0].test.__wrapped__ is fail
    assert result.failed[0].exc_info[0] is TestFailure
    assert result.succeeded[0].test.__wrapped__ is succeed


@suite.test
def conditional():
    """@Tests().test_if(condition)"""

    col = Tests(replace_tests=True)

    @col.test_if(True)
    def include():
        pass

    @col.test_if(False)
    def exclude():
        pass

    assert include in col
    assert exclude not in col


@suite.test
def unittest_compat():
    """Compatibility with Python's unittest package"""
    signals = set()

    example = Tests()

    @example.test
    def simple():
        signals.add("one")

    class Test(TestBase):
        @test
        def simple(self):
            signals.add("two")
    Test = example.register(Test)  # Python 2.5

    # unittest.TestCase
    TestCase = example.test_case()

    TestCase("test_simple").debug()
    assert signals == set(["one"])

    # unittest.TestSuite
    test_suite = example.test_suite()

    signals.clear()
    test_suite.debug()
    assert signals == set(["one", "two"])


@suite.test
def testcase_naming():
    example = Tests()

    @example.test
    def simple():
        pass

    @example.test
    def simple():
        """Duplicate name, should have ``_2`` appended."""

    class Test(TestBase):
        @test
        def simple():
            """Another duplicate, should have ``_3`` appended."""
    Test = example.register(Test)  # Python 2.5

    @example.test
    def test_something():
        """Already prepended with ``test_`` - should be used verbatim."""

    example.test(lambda self: None)

    TestCase = example.test_case()
    assert TestCase.test_simple
    assert TestCase.test_simple_2
    assert TestCase.test_simple_3
    assert TestCase.test_something
    assert TestCase.test_lambda

def unittest_wrap():
    """@Tests().unittest_wrap"""

    col = Tests()

    class UnitTestTestCase(unittest.TestCase):
        def runTest(self):
            pass
    UnitTestTestCase = col.register(UnitTestTestCase)

    assert len(col) == 1

@suite.test
def unittest_run_pass():
    """Wrapping passing TestCase"""

    col = Tests()

    class UnitTestTestCase(unittest.TestCase):
        def runTest(self):
            pass
    UnitTestTestCase = col.register(UnitTestTestCase)

    result = TestReporter()
    col.run(result)
    assert len(result.failed) == 0
    assert len(result.succeeded) == 1

@suite.test
def unittest_run_fail_assert():
    """Wrapping TestCase failing with assert"""

    col = Tests()

    class UnitTestTestCase(unittest.TestCase):
        def runTest(self):
            assert 2 + 2 == 5
    UnitTestTestCase = col.register(UnitTestTestCase)

    result = TestReporter()
    col.run(result)

    assert len(result.failed) == 1
    assert len(result.succeeded) == 0

@suite.test
def unittest_add_instance():
    """Wrapping TestCase instances"""

    col = Tests()

    class PassingUnitTestTestCase(unittest.TestCase):
        def runTest(self):
            pass
    class FailingUnitTestTestCase(unittest.TestCase):
        def runTest(self):
            assert 2 + 2 == 5

    col.register([PassingUnitTestTestCase(), FailingUnitTestTestCase()])

    result = TestReporter()
    col.run(result)

    assert len(result.failed) == 1
    assert len(result.succeeded) == 1

@suite.test
def unittest_check_setup_teardown():
    """Checking setUp/tearDown functioning"""

    col = Tests()

    class SetUpTearDownTestCase(unittest.TestCase):
        def __init__(self):
            self.set_up_invoked = False
            self.tear_down_invoked = False
            super(SetUpTearDownTestCase, self).__init__()

        def setUp(self):
            self.set_up_invoked = True
        def runTest(self):
            pass
        def tearDown(self):
            if not self.set_up_invoked:
                raise RuntimeError()
            self.tear_down_invoked = True

    t = SetUpTearDownTestCase()
    col.register([t])

    result = TestReporter()
    col.run(result)

    assert len(result.succeeded) == 1
    assert t.set_up_invoked == True
    assert t.tear_down_invoked == True

@suite.test
def unittest_check_test_functions():
    """Checking test* functions"""

    col = Tests()

    class MultiTestCase(unittest.TestCase):
        def setUp(self):
            MultiTestCase.set_up_invoked += 1
        def testFailOne(self):
            assert False
        def testFailTwo(self):
            assert False
        def testPassOne(self):
            assert True
        def testPassTwo(self):
            assert True
        def testPassThree(self):
            assert True
        def tearDown(self):
            MultiTestCase.tear_down_invoked += 1

    MultiTestCase.set_up_invoked = 0
    MultiTestCase.tear_down_invoked = 0

    col.register(MultiTestCase)

    result = TestReporter()
    col.run(result)

    assert MultiTestCase.set_up_invoked == 5
    assert MultiTestCase.tear_down_invoked == 5
    assert len(result.succeeded) == 3
    assert len(result.failed) == 2
