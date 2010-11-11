from schluck import Tests, Assert

asserts = Tests()

@asserts.test
def raises():
    try:
        with Assert.raises(RuntimeError):
            pass
    except AssertionError:
        pass
    else:
        raise AssertionError("didn't fail for missing exception")
