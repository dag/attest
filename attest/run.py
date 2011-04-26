import sys
from attest.collectors import Tests

def main():
    try:
        names = sys.argv.pop(1)
    except IndexError:
        try:
            from setuptools import find_packages
        except ImportError:
            print 'Usage: python -mattest.run <import path>'
        else:
            names = find_packages()
    Tests(names).main()

if __name__ == '__main__':
    main()
