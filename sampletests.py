from __future__ import division

import time
import random
import sys

from attest import TestBase, test, Tests, Assert


class Sample(TestBase):

    @test
    def stylish_and_classy(self):
        Assert(True).is_(False)


sample = Tests([Sample])

@sample.test
def compare():
    Assert(5) < 10

@sample.test
def contains():
    print 'Checking membership...'
    print >>sys.stderr, 'Expecting utter failure.'
    5 in Assert([1, 2, 3])

for x in xrange(16):
    @sample.test
    def passing():
        time.sleep(random.randint(1, 3) / 10)

@sample.test
def multi():
    """Multiple assertions on the same object."""
    hello = Assert('hello')
    hello.upper() == 'HELLO'
    hello.capitalize() == 'hello'

sample.main()
