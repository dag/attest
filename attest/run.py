from __future__ import with_statement

import sys
import os
from os import path

from pkg_resources import get_distribution
from optparse import OptionParser, make_option
from attest.collectors import Tests
from attest.reporters import get_all_reporters, get_reporter_by_name
from attest.utils import parse_options
from attest.hook import AssertImportHook


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
            make_option('-d', '--debugger',
                action='store_true',
                help='enter pdb for failing tests',
            ),
            make_option('-r', '--reporter',
                metavar='NAME',
                help='select reporter by name'
            ),
            make_option('-l', '--list-reporters',
                action='store_true',
                help='list available reporters'
            ),
            make_option('-n', '--no-capture',
                action='store_true',
                help="don't capture stderr and stdout"
            ),
            make_option('--full-tracebacks',
                action='store_true',
                help="don't clean tracebacks"
            ),
            make_option('--fail-fast',
                action='store_true',
                help='stop at first failure'
            ),
            make_option('--native-assert',
                action='store_true',
                help="don't hook the assert statement"
            ),
            make_option('-p', '--profile',
                metavar='FILENAME',
                help='enable tests profiling and store results in filename'
            ),
            make_option('-k', '--keyboard-interrupt',
                action='store_true',
                help="Let KeyboardInterrupt exceptions (CTRL+C) propagate"
            ),
        ]
    )
    args.update(kwargs)
    return OptionParser(**args)


def main(tests=None, **kwargs):
    parser = make_parser(**kwargs)
    options, args = parser.parse_args()

    # When run as a console script (i.e. ``attest``), the CWD isn't
    # ``sys.path[0]``, but it should be. It's important to do this early in
    # case custom reporters are being used that make the assumption that CWD is
    # on ``sys.path``.
    cwd = os.getcwd()
    if sys.path[0] not in ('', cwd):
        sys.path.insert(0, cwd)

    if options.list_reporters:
        for reporter in get_all_reporters():
            print reporter
        return

    opts = parse_options(args)
    reporter = get_reporter_by_name(options.reporter)(**opts)

    if not tests:
        names = [arg for arg in args if '=' not in arg]
        if not names:
            names = [name for name in os.listdir('.')
                          if path.isfile('%s/__init__.py' % name)]

        if options.native_assert:
            tests = Tests(names)
        else:
            with AssertImportHook():
                tests = Tests(names)

    def run():
        tests.run(reporter, full_tracebacks=options.full_tracebacks,
                            fail_fast=options.fail_fast,
                            debugger=options.debugger,
                            no_capture=options.no_capture,
                            keyboard_interrupt=options.keyboard_interrupt)

    if options.profile:
        filename = options.profile
        import cProfile
        cProfile.runctx('run()', globals(), locals(), filename)
        print 'Wrote profiling results to %r.' % (filename,)
    else:
        run()


if __name__ == '__main__':
    main()
