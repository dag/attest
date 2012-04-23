Modern Test Automation for Python
=================================

Attest is a test automation framework for Python emphasising modern idioms
and conventions.

.. code-block:: python

    from attest import Tests
    math = Tests()

    @math.test
    def arithmetics():
        """Ensure that the laws of physics are in check."""
        assert 1 + 1 == 2

    if __name__ == '__main__':
        math.run()



Features
========

* Collect tests using decorators instead of matching names against a regexp
* Set up fixtures as context managers that can be combined and reused
* Use the *assert* statement with arbitrary expressions that are inspected
  on failure
* Scan for collections by type rather than by name
* Treat tests as Python packages rather than script files
