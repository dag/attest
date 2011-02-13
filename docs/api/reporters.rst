Reporting results
=================

.. module:: attest.reporters

Reporters are in charge of handling the state and outcome of test-runs.
They might output machine- or human-readable reports on the console, or
display the results in a graphical user interface.

.. autofunction:: get_reporter_by_name

.. autofunction:: get_all_reporters


Testing on the command-line
---------------------------

.. autofunction:: auto_reporter

.. autoclass:: FancyReporter

.. autoclass:: PlainReporter


Testing from Vim (and possibly other editors)
---------------------------------------------

.. autoclass:: QuickFixReporter


Integrating testing with non-Python tools
-----------------------------------------

.. autoclass:: XmlReporter


Writing new reporters
---------------------

.. autoclass:: AbstractReporter
   :members: test_loader, begin, success, failure, finished

.. autoclass:: TestResult
   :members:
