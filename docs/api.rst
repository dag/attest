API Reference
=============

.. module:: attest


Collecting tests
----------------

.. autoclass:: Tests
   :members: test, context, register, test_suite

   .. automethod:: run(reporter=auto_reporter)

.. autoclass:: TestBase

.. autofunction:: test


Asserting conditions
--------------------

.. autoclass:: Assert
   :members: __str__, __getattr__, __call__, __getitem__,
       __eq__, __ne__, is_, is_not, __contains__, in_, not_in, __lt__, __le__,
       __gt__, __ge__, __nonzero__, __repr__

   .. autoattribute:: obj

   .. attribute:: __class__

        The class of the wrapped object, also wrapped in
        :class:`Assert`. Can be used for type testing::

            Assert('Hello World').__class__.is_(str)

   .. automethod:: raises(exception)

   .. automethod:: not_raising(exception)

.. autofunction:: assert_


Running tests with distribute
-----------------------------

.. autoclass:: Loader


Reporters
----------

.. autoclass:: AbstractReporter
   :members: begin, success, failure, finished

.. autoclass:: FancyReporter

.. autoclass:: PlainReporter

.. autoclass:: XmlReporter

.. autofunction:: auto_reporter

.. autofunction:: get_reporter_by_name
