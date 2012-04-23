Collecting Tests
================

.. module:: attest.collectors

To run :term:`tests <test>`, they must be collected in a :class:`Tests`
instance. There are many ways this can be achieved, allowing flexibility
and separation.

* Register individual functions with the :meth:`Tests.test` decorator.
* Register other :term:`collections <collection>` with
  :meth:`Tests.register` or as arguments to the constructor. A collection
  according to Attest is an iterable yielding :term:`test callables
  <test>`, this includes:

  * Lists of lambdas and function references.
  * :class:`Tests` instances.
  * Instances of subclasses of :class:`TestBase`.
  * Classes are instantiated and returned, allowing :meth:`Tests.register`
    to be used as a class decorator in Python 2.6 or later.


Using Functions
---------------

.. autoclass:: Tests
   :members: test, test_if, context, register, register_if, test_suite,
             test_case

   .. automethod:: run(reporter=auto_reporter)

   .. automethod:: main(argv=sys.argv)


Using Classes
-------------

.. autoclass:: TestBase

.. autofunction:: test

.. autofunction:: test_if
