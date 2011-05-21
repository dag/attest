Installation
============

Attest releases are tested and verified to work on CPython 2.5 up to 3.2
and on PyPy 1.5 (depending on the release, see the :doc:`changelog
</changes>`). Older versions of Python do not support all the modern
features used with Attest.

Install as usual from PyPI with either *pip* or *easy_install*:

.. sourcecode:: console

    $ pip install Attest
    $ easy_install Attest

This will also pull the two dependencies (progressbar and pygments) used
for producing fancy test reports on the command line. These are actually
optional, and if you prefer you can install Attest without them:

.. sourcecode:: console

    $ pip install --no-deps Attest
    $ easy_install -N Attest


Testing with Distribute
-----------------------

You can also write your setup script to run tests and it will also handle
test-specific dependencies such as Attest for you::

    from setuptools import setup

    setup(
        tests_require=['Attest'],
        test_loader='attest:auto_reporter.test_loader',
        test_suite='path.to.tests',
    )

This will install Attest if needed when you run tests but not when people
install your package.

.. sourcecode:: console

    $ python setup.py test


Testing with Tox
----------------

Another option is to run tests with `Tox`_ which lets you test in clean
virtual environments against multiple Python runtimes and dependency sets.

.. _Tox: http://codespeak.net/tox/

A typical :file:`tox.ini` might look something like this:

.. sourcecode:: ini

    [tox]
    envlist = py25, py26, py27, py31, py32, pypy

    [testenv]
    deps = Attest
    commands = python -mattest.run path.to.tests

Now Tox will run your tests against all the listed Python runtimes,
provided you have them installed on your machine.

.. sourcecode:: console

    $ tox
