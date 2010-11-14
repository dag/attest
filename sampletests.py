import time
import optparse

from attest import Tests, Assert, FORMATTERS


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


parser = optparse.OptionParser()
parser.add_option('-f', '--formatter', metavar='NAME', default='fancy')
parser.add_option('-s', '--color-scheme', metavar='NAME', default='trac')
options, args = parser.parse_args()

formatter = FORMATTERS[options.formatter]
if options.formatter == 'fancy':
    formatter = formatter(options.color_scheme)


sample.run(formatter)
