from schluck import Tests, Assert
import time

math = Tests()

@math.test
def arithmetics():
    """Test that basic arithmetics don't make sense."""
    time.sleep(.1)
    Assert(1 + 1) == 3

@math.test
def compare():
    time.sleep(.1)
    Assert(5) < 10

@math.test
def contains():
    time.sleep(.1)
    2 in Assert([1,2,3])

for x in xrange(17):
    @math.test
    def passing():
        time.sleep(.1)

if __name__ == '__main__':
    math.run()
