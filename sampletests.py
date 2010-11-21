from __future__ import division

import time
import random
import sys
import optparse

from attest import Tests, Assert, get_reporter_by_name


sample = Tests()

@sample.test
def compare():
    Assert(5) < 10

@sample.test
def contains():
    print 'Checking membership...'
    print >>sys.stderr, 'Expecting utter failure.'
    5 in Assert([1, 2, 3])

for x in xrange(17):
    @sample.test
    def passing():
        time.sleep(random.randint(1, 3) / 10)

@sample.test
def multi():
    """Multiple assertions on the same object."""
    hello = Assert('hello')
    hello.upper() == 'HELLO'
    hello.capitalize() == 'hello'


parser = optparse.OptionParser()
parser.add_option('-r', '--reporter', metavar='NAME', default='auto')
parser.add_option('-s', '--color-scheme', metavar='NAME', default='trac')
options, args = parser.parse_args()

reporter = get_reporter_by_name(options.reporter)
if options.reporter in ('auto', 'fancy'):
    reporter = reporter(options.color_scheme)


sample.run(reporter)
