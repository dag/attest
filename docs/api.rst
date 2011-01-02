API Reference
=============

.. module:: attest


Collecting tests
----------------

To run tests, they must be collected in a :class:`Tests` instance. There
are many ways this can be achieved, allowing flexibility and separation.

* Register individual functions with the :meth:`Tests.test` decorator.
* Register other collections with :meth:`Tests.register` or as arguments to
  the constructor. A collection according to Attest is an iterable yielding
  test callables, this includes:

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
   :members:
       isinstance, not_isinstance, issubclass, not_issubclass, json, css,
       xpath, __str__, __getattr__, __call__, __getitem__, __eq__, __ne__,
       is_, is_not, __contains__, in_, not_in, __lt__, __le__, __gt__,
       __ge__, __nonzero__, __repr__

   .. autoattribute:: obj

   .. attribute:: __class__

        The class of the wrapped object, also wrapped in
        :class:`Assert`. Can be used for type testing::

            Assert('Hello World').__class__.is_(str)

   .. automethod:: raises(exceptions)

   .. automethod:: not_raising(exception)

.. autofunction:: assert_

.. autofunction:: capture_output()


Running tests with distribute
-----------------------------

.. autoclass:: Loader


Reporters
----------

Reporters are in charge of handling the state and outcome of test-runs.
They might output machine- or human-readable reports on the console, or
display the results in a graphical user interface.

.. autoclass:: AbstractReporter
   :members: begin, success, failure, finished

.. autoclass:: FancyReporter

.. autoclass:: PlainReporter

.. autoclass:: XmlReporter

.. autofunction:: auto_reporter

.. autofunction:: get_reporter_by_name
