import sys
from attest.collectors import Tests

if __name__ == '__main__':
    try:
        name = sys.argv.pop(1)
    except IndexError:
        print 'Usage: python -mattest.run <import path>'
    else:
        Tests([name]).main()
