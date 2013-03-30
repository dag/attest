Running tests
=============

In the :doc:`quickstart </quickstart>` guide, tests were run by treating them as scripts and calling :meth:`Tests.run()` directly on the test suite. When your tests grow beyond a single file, however, you may want to use the :command:`attest` command line tool.

Usage
-----

::

    $ attest [options] [tests...] [key=value...]

The positional ``tests`` are dotted names for modules or packages that are scanned 
recursively for :class:`Tests` instances, or dotted names for any other object that 
iterates over tests. If no position arguments are provided, all packages in the 
working directory are scanned.

The key/value pairs are passed to the reporter constructor, after some command-line 
friendly parsing.

Options
"""""""

.. program:: attest

.. cmdoption:: -d, --debugger

Enter pdb for failing tests.

.. cmdoption:: -r NAME, --reporter=NAME

Select reporter by name.

.. cmdoption:: -l, --list-reporters

List available reporters.

.. cmdoption:: -n, --no-capture

Don't capture stderr and stdout.

.. cmdoption:: --full-tracebacks

Don't clean tracebacks.

.. cmdoption:: --fail-fast

Stop at first failure.

.. cmdoption:: --native-assert

Don't hook the assert statement.

.. cmdoption:: -p FILENAME, --profile=FILENAME

Enable tests profiling and store results in filename.

.. cmdoption:: -k, --keyboard-interrupt

Let KeyboardInterrupt exceptions (CTRL+C) propagate.

.. cmdoption:: --version

Show program's version number and exit.

.. cmdoption:: -h, --help

Display a help message and exit.


