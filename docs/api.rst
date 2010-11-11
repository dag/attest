API Reference
=============

.. module:: schluck

.. autoclass:: Tests
   :members: test, context, register, run

.. autoclass:: Assert
   :members: in_, not_in, is_, is_not

   .. automethod:: raises(exception)

.. autoclass:: AbstractFormatter
   :members: success, failure, finished

.. autoclass:: FancyFormatter

.. autoclass:: PlainFormatter
