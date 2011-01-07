API Reference
=============

.. module:: attest


Collecting tests
----------------

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

.. autoclass:: Tests
   :members: test, test_if, context, register, register_if, test_suite

   .. automethod:: run(reporter=auto_reporter)

   .. automethod:: main(argv=sys.argv)

.. autoclass:: TestBase

.. autofunction:: test

.. autofunction:: test_if


Asserting conditions
--------------------

.. autoclass:: Assert

   .. autoattribute:: obj


   .. rubric:: Conditional tests

   The normal conditional operators are supported:

   * Equality: ``==`` and ``!=``
   * Comparison: ``<``, ``<=``, ``>``, ``>=``

   Some keywords are also supported:

   * Containment: ``in``, but beware that it is the container that should
     be wrapped and that the negated form, ``not in``, will *not* work.

   These operators and keywords are **not** natively supported:

   * Identity: ``is``, ``is not``
   * Negative containment: ``not in``

   They are instead supported via the following methods.

   .. automethod:: is_

   .. automethod:: is_not

   .. automethod:: in_

   .. automethod:: not_in


   .. rubric:: Convinient helpers

   .. autoattribute:: json

   .. automethod:: css

   .. automethod:: xpath


   .. rubric:: Static methods

   .. automethod:: raises(\*exceptions)

   .. automethod:: not_raising(\*exception)

   .. automethod:: isinstance

   .. automethod:: not_isinstance

   .. automethod:: issubclass

   .. automethod:: not_issubclass


   .. rubric:: Proxying

   Item and attribute access is proxied to the wrapped object, however in
   the latter case this can be unpredictable due to the wrapper class
   having its own attributes. Therefore there is a method for this, too.

   .. automethod:: attr

   .. automethod:: passed_to


.. autofunction:: assert_

.. autofunction:: capture_output()

.. autofunction:: disable_imports(\*names)


Running tests with distribute
-----------------------------

.. autoclass:: Loader


Reporters
----------

Reporters are in charge of handling the state and outcome of test-runs.
They might output machine- or human-readable reports on the console, or
display the results in a graphical user interface.

.. autofunction:: get_reporter_by_name

.. autofunction:: get_all_reporters

.. autofunction:: auto_reporter

.. autoclass:: FancyReporter

.. autoclass:: PlainReporter

.. autoclass:: XmlReporter

.. autoclass:: AbstractReporter
   :members: begin, success, failure, finished

.. autoclass:: TestResult
   :members:
