from schluck import Tests, Assert

math = Tests()

@math.test
def arithmetics():
    """Test that basic arithmetics don't make sense."""
    Assert(1 + 1) == 3

@math.test
def compare():
    Assert(5) > 10

if __name__ == '__main__':
    math.run()
