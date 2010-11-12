API Reference
=============

.. module:: schluck


Collecting tests
----------------

.. autoclass:: Tests
   :members: test, context, register, test_suite, run

.. autoclass:: TestBase

.. autofunction:: test


Asserting conditions
--------------------

.. autoclass:: Assert
   :members: in_, not_in, is_, is_not

   .. automethod:: raises(exception)


Running tests with distribute
-----------------------------

.. autoclass:: Loader


Formatters
----------

.. autoclass:: AbstractFormatter
   :members: success, failure, finished

.. autoclass:: FancyFormatter

.. autoclass:: PlainFormatter
