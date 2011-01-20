import sys
from .collectors import Tests

if __name__ == '__main__':
    try:
        name = sys.argv.pop(1)
    except IndexError:
        print 'Usage: python -mattest <import path>'
    else:
        Tests([name]).main()
