from schluck import Tests, Assert
import time

sample = Tests()

@sample.test
def arithmetics():
    """Test that basic arithmetics don't make sense."""
    time.sleep(.1)
    Assert(1 + 1) == 3

@sample.test
def compare():
    time.sleep(.1)
    Assert(5) < 10

@sample.test
def contains():
    time.sleep(.1)
    5 in Assert([1, 2, 3])

for x in xrange(17):
    @sample.test
    def passing():
        time.sleep(.1)

if __name__ == '__main__':
    sample.run()
