API Reference
=============

.. module:: attest


Collecting tests
----------------

.. autoclass:: Tests
   :members: test, context, register, test_suite

   .. automethod:: run(formatter=auto_formatter)

.. autoclass:: TestBase

.. autofunction:: test


Asserting conditions
--------------------

.. autoclass:: Assert
   :members: in_, not_in, is_, is_not

   .. automethod:: raises(exception)

.. autofunction:: assert_


Running tests with distribute
-----------------------------

.. autoclass:: Loader


Formatters
----------

.. autoclass:: AbstractFormatter
   :members: begin, success, failure, finished

.. autoclass:: FancyFormatter

.. autoclass:: PlainFormatter

.. autofunction:: auto_formatter
