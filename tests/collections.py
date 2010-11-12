from schluck import AbstractFormatter, Tests, Assert


class Failure(object):

    def __init__(self, test, error, traceback):
        self.test = Assert(test)
        self.error = Assert(error)
        self.traceback = Assert(traceback)


class TestFormatter(AbstractFormatter):

    def __init__(self, tests):
        self.succeeded = []
        self.failed = []

    def success(self, test):
        self.succeeded.append(Assert(test))

    def failure(self, test, error, traceback):
        self.failed.append(Failure(test, error, traceback))

    def finished(self):
        pass


collections = Tests()

@collections.test
def decorator():

    col = Tests()

    @col.test
    def one(): pass

    @col.test
    def two(): pass

    Assert(len(col)) == 2
    Assert(list(col)) == [one, two]

@collections.test
def context():

    col = Tests()

    @col.test
    def test(calculated):
        Assert(calculated) == 2

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

    col3 = Tests()

    @col3.context
    def multiple():
        yield 1, 2, 3

    @col3.test
    def test3(one, two, three):
        Assert(one) == 1
        Assert(two) == 2
        Assert(three) == 3

    test3()

@collections.test
def run():

    col = Tests()

    @col.test
    def fail():
        Assert(1) == 2

    @col.test
    def succeed():
        Assert(1) == 1

    result = TestFormatter(col)
    with Assert.raises(SystemExit):
        col.run(result)

    Assert(len(result.failed)) == 1
    Assert(len(result.succeeded)) == 1

    result.failed[0].test.is_(fail)
    result.failed[0].error.__class__.is_(AssertionError)
    result.succeeded[0].is_(succeed)
