Reporters
=========

.. module:: attest.reporters

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
