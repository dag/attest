Hooking the assert statement
============================

The most natural way to write test conditions in Python is the
:keyword:`assert` statement, but a downside to it is that it doesn't let
you know the values used in the conditional expression that failed. This
makes debugging test failures more difficult as you can't easily tell *why*
the test failed, only that it did.

Attest includes a hook for the assert statement, the effect of which is
that assert expressions can be analyzed and inspected. Using it is easy,
just import it in the test modules you wish to use it in, and make sure
Attest is imported before your tests (this is already the case in most
setups)::

    from attest import assert_hook
    assert str(2 + 2) == '5'

If used in a test, the above assertion would in Attest result in output
including ``assert (str(4) == '5')`` which tells you the result of ``2 +
2``. This works also to expand the values of variables.

If you're having issues with the assert hook on CPython 2.5, it is likely
due to its inability to compile AST nodes to code objects. You can disable
the hook conditionally by the presence of this capability easily::

    from attest import AssertImportHook, COMPILES_AST
    if not COMPILES_AST:
        AssertImportHook.disable()

By default, the hook is enabled when Attest is first imported. If Python
can't compile AST nodes and the hook is enabled, Attest tries to render the
AST into source code for compilation, which works but loses the line
numbers metadata in tracebacks.

.. module:: attest.hook

.. autofunction:: assert_hook

.. autoclass:: AssertImportHook
    :members:

Low-level utilities
-------------------

.. autoclass:: ExpressionEvaluator
    :members:

.. autoclass:: AssertTransformer
    :members:
