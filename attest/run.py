from pkg_resources import get_distribution
from optparse import OptionParser
from attest.collectors import Tests
from attest.reporters import get_all_reporters, get_reporter_by_name


def main(tests=None):
    parser = OptionParser(usage='attest [options] [tests...]',
                          version=get_distribution('Attest').version,
                          description=
                              'The positional "tests" are dotted '
                              'names for modules or packages that are scanned '
                              'recursively for Tests instances, or dotted names '
                              'for any other object that iterates over tests. If '
                              'not provided, packages in the working directory '
                              'are scanned.')
    parser.add_option('-r', '--reporter', metavar='NAME',
                      help='select reporter by name')
    parser.add_option('--full-tracebacks', action='store_true',
                      help="don't clean tracebacks")
    parser.add_option('-l', '--list-reporters', action='store_true',
                      help='list available reporters')
    options, args = parser.parse_args()

    if options.list_reporters:
        for reporter in get_all_reporters():
            print reporter
        return

    reporter = get_reporter_by_name(options.reporter)()

    if not tests:
        if args:
            tests = Tests(args)
        else:
            try:
                from setuptools import find_packages
            except ImportError:
                parser.print_help()
            else:
                tests = Tests(find_packages())

    tests.run(reporter, full_tracebacks=options.full_tracebacks)


if __name__ == '__main__':
    main()
