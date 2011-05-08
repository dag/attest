import sys
import os
from os import path

from pkg_resources import get_distribution
from optparse import OptionParser, make_option
from attest.collectors import Tests
from attest.reporters import get_all_reporters, get_reporter_by_name
from attest.utils import parse_options


def make_parser(**kwargs):
    args = dict(
        prog='attest',
        usage='%prog [options] [tests...] [key=value...]',
        version=get_distribution('Attest').version,

        description=(
            'The positional "tests" are dotted '
            'names for modules or packages that are scanned '
            'recursively for Tests instances, or dotted names '
            'for any other object that iterates over tests. If '
            'not provided, packages in the working directory '
            'are scanned.\n'
            'The key/value pairs are passed to the '
            'reporter constructor, after some command-line '
            'friendly parsing.'
        ),

        option_list=[
            make_option('-r', '--reporter',
                metavar='NAME',
                help='select reporter by name'
            ),
            make_option('--full-tracebacks',
                action='store_true',
                help="don't clean tracebacks"
            ),
            make_option('-l', '--list-reporters',
                action='store_true',
                help='list available reporters'
            )
        ]
    )
    args.update(kwargs)
    return OptionParser(**args)


def main(tests=None, **kwargs):
    parser = make_parser(**kwargs)
    options, args = parser.parse_args()

    if options.list_reporters:
        for reporter in get_all_reporters():
            print reporter
        return

    opts = parse_options(args)
    reporter = get_reporter_by_name(options.reporter)(**opts)

    if not tests:
        sys.path.insert(0, os.getcwd())
        args = [arg for arg in args if '=' not in arg]
        if args:
            tests = Tests(args)
        else:
            packages = [name for name in os.listdir('.')
                             if path.isfile('%s/__init__.py' % name)]
            tests = Tests(packages)

    tests.run(reporter, full_tracebacks=options.full_tracebacks)


if __name__ == '__main__':
    main()
