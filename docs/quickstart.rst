Quickstart
==========

.. warning::

    This document is outdated, incomplete and generally needs love. It
    might serve to give you an idea of how to use Attest but you're better
    of reading the API reference for most purposes.

.. currentmodule:: attest

Because mathematics never lie, except when it claims ``0.9… = 1``, we'll be
testing math in this quickstart.

*Attest* is quite agnostic and doesn't enforce any particular setup, but for
sake of simplicity and because I'm only making Attest flexible in a
self-defeating impulse of compulsive behaviour, I'll tell you how *I* like to
write tests, and how that is done with Attest.

First of all, you should know that Attest will not do any automatic discovery
of tests behind your back. You're in control. Sit back and relax. If you worry
about boilerplate I can assure you it is minimal.

Second, there is no global collection of tests. This is related to the
previous point. *You* write your test collections, and bind them together
when you want to run more than a specific one.

Third, because of the above points, no particular directory structure or
naming conventions are enforced. A collection of tests is just a Python
package. You control what should be included by importing and registering
collections. When you run tests, just point to them.


The most low-level assumptions
------------------------------

*Attest* follows a few assumptions meant to make the core flexible.

* A test is a callable object that takes no arguments.
* A failure is an unhandled exception, or a return value of :const:`False`.
* A collection is an iterable object yielding test objects.

Effectively, while perhaps practically not very useful, this implies you can
write a list of lambda expressions as a test collection.


The more high-level toolbox
---------------------------

Attest provides a few tools to aid in the creation of tests and collections,
abiding to the above assumptions. Each tool is carefully designed to follow
idiomatic Python conventions and to solve the particular problem of testing
with "the right tool for the job".

My favourite is the functional API inspired by `Flask`_. Classes
don't really make sense unless you're going to have multiple instances or
you're using inheritance for something. The functional API is flat, which
ultimately is a desirable idiom in Python. Flat implies functions defined
in the top-level rather than methods wrapped in a class. This saves you some
indentation levels, by extension giving you more characters within the
conventional limit of 80. Mostly, and more importantly, it makes sense because
classes don't.

Because taste varies, and for the rare situations when classes do make sense,
there is support for the use of tests wrapped in a class. These however are
quite unlike the test classes of the unittest library — rather than modelling
a Java package they, too, closely follow conventional Python idioms.

.. _Flask: http://flask.pocoo.org/


Functional style
----------------

In functional style, we make an instance of :class:`Tests` and add
tests to it with a decorator method on the instance.

.. centered:: tests/math.py

::

    from attest import Tests

    math = Tests()

    @math.test
    def arithmetics():
        assert 1 + 1 == 2

Optionally, we add this at the end to be able to run this collection
alone::

    if __name__ == '__main__':
        math.main()

.. code-block:: text

    $ python tests/math.py
    1 of 1 [Time: 00:00:00|#########################################|100%]

    Failures: 0/1 (0 assertions)

Wait a minute, zero assertions? It's because we're using :keyword:`assert`
which attest can't detect. To have the assertion counted you can use
:func:`assert_` instead::

    assert_(1 + 1 == 2)

.. code-block:: text

    Failures: 0/1 (1 assertions)

That's better, but what happens on failure?

::

    value = 1 + 1
    assert_(value == 3)

.. code-block:: pytb

    arithmetics
    ──────────────────────────────────────────────────────────────────────
    Traceback (most recent call last):
      File "math.py", line 8, in arithmetics
        assert_(value == 3)
    AssertionError

The value of the variable is hidden from us making it harder to debug
failed tests, that's no good! :class:`Assert` to the rescue - by
wrapping the value we can have better failure reports using operator
overloading:

.. warning::

    :class:`Assert` will not behave properly with the :keyword:`is` or
    ``not in`` operations because we can't override those. Instead use the
    :meth:`~Assert.is_`, :meth:`~Assert.is_not` and :meth:`~Assert.not_in`
    methods. For consistency there's also an :meth:`~Assert.in_` method.

    Operations that do work: ``==``, ``!=``. :keyword:`in`, ``<``, ``<=``,
    ``>`` and ``>=``. :class:`Assert` also does a lot more, see the API
    documentation.

::

    value = Assert(1 + 1)
    assert value == 3

.. code-block:: pytb

    arithmetics
    ──────────────────────────────────────────────────────────────────────
    Traceback (most recent call last):
      File "math.py", line 8, in arithmetics
        assert value == 3
    AssertionError: 2 != 3

That's more like it!

.. note::

    It's not necessary to use :keyword:`assert` with :class:`Assert` but it
    can help readability and avoids some mistakes that would otherwise make
    tests pass silently, for example if an object unexpectedly is not wrapped
    in :class:`Assert`.

How about testing the same precomputed value in multiple tests? In other
testing frameworks we'd use setup and teardown; Attest uses context
managers via :meth:`Tests.context`::

    @math.context
    def compute_value():
        value = 1 + 1
        yield value

The value will now be passed to tests in the ``math`` collection, as an
argument::

    @math.test
    def value_of_value(value):
        Assert(value) == 2

Now lets set up our tests so we can combine many collections into one.

.. centered:: tests/__init__.py

::

    from attest import Tests
    from tests.math import math

    tests = Tests([math])

As you make more collections, just import them here and add to the list.

.. centered:: runtests.py

::

    from tests import tests
    tests.main()

With this we can run the full suite with ``python runtests.py``.


Object-oriented style
---------------------

If you prefer to write test collections as classes, there's an API for
that. Here's the above example in object-oriented style:

.. centered:: tests/math.py

::

    from attest import TestBase, test, Assert

    class Math(TestBase):

        def __context__(self):
            self.value = 1 + 1
            yield

        @test
        def arithmetics(self):
            Assert(self.value) == 2

.. centered:: tests/__init__.py

::

    from attest import Tests
    from tests.math import Math

    tests = Tests([Math])

You can also list instances and have your own ``__init__()`` to create
different tests from the same collection.
