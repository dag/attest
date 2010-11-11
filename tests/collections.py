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
