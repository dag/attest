Reporting Results
=================

.. module:: attest.reporters

Reporters are in charge of handling the state and outcome of test-runs.
They might output machine- or human-readable reports on the console, or
display the results in a graphical user interface.

.. autofunction:: get_reporter_by_name

.. autofunction:: get_all_reporters


Testing from the Command-Line
-----------------------------

.. autofunction:: auto_reporter

.. autoclass:: FancyReporter

.. autoclass:: PlainReporter


Testing from the Editor
-----------------------

This is known to work with Vim, but can probably be used with other editors
as well. The output mimics that used by many compilers for errors and
warnings.

.. autoclass:: QuickFixReporter


Integrating Testing with Non-Python Tools
-----------------------------------------

.. autoclass:: XmlReporter


Writing New Reporters
---------------------

.. autoclass:: AbstractReporter
   :members: test_loader, begin, success, failure, finished

.. autoclass:: TestResult
   :members:
