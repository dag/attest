Glossary
========

.. currentmodule:: attest

.. glossary::

    assertive object
        An object that is wrapped in :class:`~attest.deprecated.Assert` and
        which will raise :exc:`AssertionError` for comparative operations
        that are :const:`False`.

        .. deprecated:: 0.5

    reporter
        Event handler for test-runs, notified of the outcome of each test.

    test
        Callable object that takes no arguments and might :term:`fail
        <failure>`.

    failure
        Unhandled exception or a return value of :const:`False`.

    collection
        Iterable yielding :term:`tests <test>`.
