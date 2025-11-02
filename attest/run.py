import argparse
import os
import sys
from importlib.metadata import version
from os import path

from attest.collectors import Tests
from attest.hook import AssertImportHook
from attest.reporters import get_all_reporters, get_reporter_by_name
from attest.utils import parse_options


def make_parser(**kwargs):
    parser_kwargs = {
        'prog': 'attest',
        'usage': '%(prog)s [options] [tests...] [key=value...]',
        'description': (
            'The positional "tests" are dotted '
            'names for modules or packages that are scanned '
            'recursively for Tests instances, or dotted names '
            'for any other object that iterates over tests. If '
            'not provided, packages in the working directory '
            'are scanned. '
            'The key/value pairs are passed to the '
            'reporter constructor, after some command-line '
            'friendly parsing.'
        ),
    }
    parser_kwargs.update(kwargs)
    parser = argparse.ArgumentParser(**parser_kwargs)

    # Add version argument
    parser.add_argument(
        '--version',
        action='version',
        version=f"%(prog)s {version('attest')}"
    )

    # Add optional arguments
    parser.add_argument(
        '-d', '--debugger',
        action='store_true',
        help='enter pdb for failing tests',
    )
    parser.add_argument(
        '-r', '--reporter',
        metavar='NAME',
        help='select reporter by name'
    )
    parser.add_argument(
        '-l', '--list-reporters',
        action='store_true',
        help='list available reporters'
    )
    parser.add_argument(
        '-n', '--no-capture',
        action='store_true',
        help="don't capture stderr and stdout"
    )
    parser.add_argument(
        '--full-tracebacks',
        action='store_true',
        help="don't clean tracebacks"
    )
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='stop at first failure'
    )
    parser.add_argument(
        '--native-assert',
        action='store_true',
        help="don't hook the assert statement"
    )
    parser.add_argument(
        '-p', '--profile',
        metavar='FILENAME',
        help='enable tests profiling and store results in filename'
    )
    parser.add_argument(
        '-k', '--keyboard-interrupt',
        action='store_true',
        help="Let KeyboardInterrupt exceptions (CTRL+C) propagate"
    )

    # Add positional arguments (tests and key=value pairs)
    parser.add_argument(
        'args',
        nargs='*',
        help='test modules/packages and key=value options'
    )

    return parser


def main(tests=None, **kwargs):
    parser = make_parser(**kwargs)
    args = parser.parse_args()

    # When run as a console script (i.e. ``attest``), the CWD isn't
    # ``sys.path[0]``, but it should be. It's important to do this early in
    # case custom reporters are being used that make the assumption that CWD is
    # on ``sys.path``.
    cwd = os.getcwd()
    if sys.path[0] not in ('', cwd):
        sys.path.insert(0, cwd)

    if args.list_reporters:
        for reporter in get_all_reporters():
            print(reporter)
        return

    opts = parse_options(args.args)
    reporter = get_reporter_by_name(args.reporter)(**opts)

    if not tests:
        names = [arg for arg in args.args if '=' not in arg]
        if not names:
            names = [name for name in os.listdir('.')
                          if path.isfile(f'{name}/__init__.py')]

        if args.native_assert:
            tests = Tests(names)
        else:
            with AssertImportHook():
                tests = Tests(names)

    def run():
        tests.run(
            reporter,
            full_tracebacks=args.full_tracebacks,
            fail_fast=args.fail_fast,
            debugger=args.debugger,
            no_capture=args.no_capture,
            keyboard_interrupt=args.keyboard_interrupt,
        )

    if args.profile:
        filename = args.profile
        import cProfile
        cProfile.runctx('run()', globals(), locals(), filename)
        print(f'Wrote profiling results to {filename!r}.')
    else:
        run()


if __name__ == '__main__':
    main()
