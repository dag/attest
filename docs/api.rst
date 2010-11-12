API Reference
=============

.. module:: schluck

.. autoclass:: Tests
   :members: test, context, register, run

.. autoclass:: TestBase

.. autofunction:: test

.. autoclass:: Assert
   :members: in_, not_in, is_, is_not

   .. automethod:: raises(exception)

.. autoclass:: Loader

.. autoclass:: AbstractFormatter
   :members: success, failure, finished

.. autoclass:: FancyFormatter

.. autoclass:: PlainFormatter
