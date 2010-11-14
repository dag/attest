How to attest to the correctness of an application
==================================================

.. sidebar:: Directory structure

    * runtests.py

    * tests/

      * __init__.py
      * math.py


Because mathematics never lie, except when it claims ``0.9… = 1``, we'll be
testing math in this guide.

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
