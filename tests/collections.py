from schluck import Tests, Assert

collections = Tests()

@collections.test
def decorator():

    col = Tests()

    @col.test
    def one(): pass

    @col.test
    def two(): pass

    Assert(len(col.tests)) == 2
    Assert(col.tests) == [one, two]

@collections.test
def context():

    col = Tests()

    @col.test
    def test(calculated):
        Assert(calculated) == 2

    @col.context
    def context():
        calculated = 1 + 1
        yield calculated,

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
