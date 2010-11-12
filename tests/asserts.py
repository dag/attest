from __future__ import with_statement

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

@asserts.test
def equality():
    Assert(1) == 1
    Assert(1) != 0
    with Assert.raises(AssertionError):
        Assert(1) == 0
    with Assert.raises(AssertionError):
        Assert(1) != 1

@asserts.test
def compare():
    Assert(1) > 0
    Assert(0) < 1
    Assert(1) >= 0
    Assert(1) >= 1
    Assert(0) <= 0
    Assert(0) <= 1
    with Assert.raises(AssertionError):
        Assert(0) > 1
    with Assert.raises(AssertionError):
        Assert(1) < 0
    with Assert.raises(AssertionError):
        Assert(0) >= 1
    with Assert.raises(AssertionError):
        Assert(0) >= 1
    with Assert.raises(AssertionError):
        Assert(1) <= 0
    with Assert.raises(AssertionError):
        Assert(1) <= 0

@asserts.test
def contains():
    1 in Assert([0,1,2])
    Assert(1).in_([0,1,2])
    Assert(3).not_in([0,1,2])
    with Assert.raises(AssertionError):
        3 in Assert([0,1,2])
    with Assert.raises(AssertionError):
        Assert(3).in_([0,1,2])
    with Assert.raises(AssertionError):
        Assert(1).not_in([0,1,2])

@asserts.test
def identity():
    Assert(True).is_(True)
    Assert(False).is_not(True)
    Assert([]).is_not([])
    with Assert.raises(AssertionError):
        Assert(False).is_(True)
    with Assert.raises(AssertionError):
        Assert(True).is_not(True)
    with Assert.raises(AssertionError):
        Assert([]).is_([])

@asserts.test
def proxy():
    hello = Assert('hello')
    hello == 'hello'
    hello.upper() == 'HELLO'
    with Assert.raises(AssertionError):
        hello.upper() == 'hello'

@asserts.test
def boolean():
    bool(Assert(1))
    assert Assert(1)
    with Assert.raises(AssertionError):
        bool(Assert(0))
        assert Assert(0)
