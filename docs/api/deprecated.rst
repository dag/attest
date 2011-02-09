Deprecated utilities
====================

.. module:: attest.deprecated

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


.. autoclass:: Loader
