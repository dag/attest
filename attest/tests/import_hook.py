"""Comprehensive tests for the AssertImportHook functionality."""
import os
import sys
import tempfile
import shutil
from contextlib import contextmanager

from attest import Tests, assert_hook
from attest.hook import AssertImportHook, AssertTransformer, TestFailure


suite = Tests()


@contextmanager
def temp_module(name, source, package=False):
    """Create a temporary module for testing.

    :param name: Module name (can include dots for submodules)
    :param source: Python source code
    :param package: If True, create as a package with __init__.py
    """
    tmpdir = tempfile.mkdtemp()
    sys.path.insert(0, tmpdir)

    try:
        parts = name.split('.')
        if package:
            # Create package structure
            pkg_path = os.path.join(tmpdir, *parts)
            os.makedirs(pkg_path, exist_ok=True)
            filepath = os.path.join(pkg_path, '__init__.py')
        else:
            # Create regular module
            if len(parts) > 1:
                pkg_path = os.path.join(tmpdir, *parts[:-1])
                os.makedirs(pkg_path, exist_ok=True)
            filepath = os.path.join(tmpdir, *parts[:-1], parts[-1] + '.py')

        with open(filepath, 'w') as f:
            f.write(source)

        yield filepath
    finally:
        # Clean up
        sys.path.remove(tmpdir)
        # Remove from sys.modules
        for key in list(sys.modules.keys()):
            if key.startswith(name):
                del sys.modules[key]
        shutil.rmtree(tmpdir, ignore_errors=True)


@suite.test
def hook_enabled_disabled():
    """Test enable/disable functionality."""
    # Ensure we start with hook enabled
    AssertImportHook.enable()

    # Use direct boolean check to avoid assert hook rewriting
    if not AssertImportHook.enabled:
        raise AssertionError("Hook should be enabled after enable()")

    # Disable and check
    AssertImportHook.disable()
    if AssertImportHook.enabled:
        raise AssertionError("Hook should be disabled after disable()")

    # Enable and check
    AssertImportHook.enable()
    if not AssertImportHook.enabled:
        raise AssertionError("Hook should be enabled after second enable()")

    # Calling enable twice should not cause issues
    AssertImportHook.enable()
    if not AssertImportHook.enabled:
        raise AssertionError("Hook should still be enabled after third enable()")


@suite.test
def hook_as_context_manager():
    """Test using AssertImportHook as a context manager."""
    # Disable first
    AssertImportHook.disable()
    assert AssertImportHook.enabled is False

    # Use as context manager
    with AssertImportHook():
        assert AssertImportHook.enabled is True

    # Should be disabled again after exiting
    assert AssertImportHook.enabled is False

    # Re-enable for other tests
    AssertImportHook.enable()


@suite.test
def rewrite_simple_assertion():
    """Test that simple assertions are rewritten."""
    with temp_module('test_simple', '''
from attest import assert_hook

def test_func():
    x = 1
    assert x == 2
'''):
        with AssertImportHook():
            import test_simple
            try:
                test_simple.test_func()
                assert False, "Should have raised TestFailure"
            except TestFailure as e:
                # Check that the assertion was rewritten and captured
                assert e.value is not None
                assert 'x == 2' in str(e.value) or '1 == 2' in str(e.value)


@suite.test
def rewrite_assertion_with_message():
    """Test that assertions with messages are rewritten."""
    with temp_module('test_message', '''
from attest import assert_hook

def test_func():
    assert False, "Custom error message"
'''):
        with AssertImportHook():
            import test_message
            try:
                test_message.test_func()
                assert False, "Should have raised TestFailure"
            except TestFailure as e:
                assert str(e) == "Custom error message"


@suite.test
def no_rewrite_without_assert_hook_import():
    """Test that modules without assert_hook import are not rewritten."""
    with temp_module('test_no_hook', '''
def test_func():
    assert False, "Standard assertion"
'''):
        with AssertImportHook():
            import test_no_hook
            try:
                test_no_hook.test_func()
                assert False, "Should have raised AssertionError"
            except AssertionError as e:
                # Should be a regular AssertionError, not TestFailure
                assert type(e).__name__ == 'AssertionError'
                assert str(e) == "Standard assertion"


@suite.test
def package_with_assert_hook():
    """Test that packages with __init__.py are handled correctly."""
    with temp_module('test_pkg', '''
from attest import assert_hook

value = 42

assert value == 42  # This should not fail
''', package=True):
        with AssertImportHook():
            import test_pkg
            assert test_pkg.value == 42


@suite.test
def package_with_submodule():
    """Test that packages with submodules work correctly."""
    tmpdir = tempfile.mkdtemp()
    sys.path.insert(0, tmpdir)

    try:
        # Create package structure
        pkg_path = os.path.join(tmpdir, 'test_pkg2')
        os.makedirs(pkg_path)

        # Create __init__.py with assert_hook
        with open(os.path.join(pkg_path, '__init__.py'), 'w') as f:
            f.write('from attest import assert_hook\n')

        # Create submodule
        with open(os.path.join(pkg_path, 'submod.py'), 'w') as f:
            f.write('from attest import assert_hook\nvalue = 123\n')

        with AssertImportHook():
            import test_pkg2
            from test_pkg2 import submod
            assert submod.value == 123
    finally:
        sys.path.remove(tmpdir)
        for key in list(sys.modules.keys()):
            if key.startswith('test_pkg2'):
                del sys.modules[key]
        shutil.rmtree(tmpdir, ignore_errors=True)


@suite.test
def module_already_imported():
    """Test that already imported modules are returned from cache."""
    with temp_module('test_cached', '''
from attest import assert_hook
value = 999
'''):
        with AssertImportHook():
            import test_cached
            first_import = test_cached

            # Import again
            import test_cached
            second_import = test_cached

            # Should be the same module object
            assert first_import is second_import
            assert test_cached.value == 999


@suite.test
def assert_transformer_should_rewrite():
    """Test AssertTransformer.should_rewrite property."""
    # Source with assert_hook import
    source_with_hook = '''
from attest import assert_hook

def test():
    assert True
'''
    transformer = AssertTransformer(source_with_hook, '<test>')
    assert transformer.should_rewrite is True

    # Source without assert_hook import
    source_without_hook = '''
def test():
    assert True
'''
    transformer = AssertTransformer(source_without_hook, '<test>')
    assert transformer.should_rewrite is False

    # Source with different import
    source_other_import = '''
from attest import Tests

def test():
    assert True
'''
    transformer = AssertTransformer(source_other_import, '<test>')
    assert transformer.should_rewrite is False


@suite.test
def assert_transformer_make_module():
    """Test AssertTransformer.make_module creates valid modules."""
    source = '''
from attest import assert_hook
x = 100
'''
    transformer = AssertTransformer(source, '<test>')
    module = transformer.make_module('test_make_module')

    # Check module is in sys.modules
    assert 'test_make_module' in sys.modules
    assert sys.modules['test_make_module'] is module

    # Check module attributes
    assert hasattr(module, 'x')
    assert module.x == 100

    # Clean up
    del sys.modules['test_make_module']


@suite.test
def complex_assertion_expressions():
    """Test that complex assertion expressions are rewritten correctly."""
    with temp_module('test_complex', '''
from attest import assert_hook

def test_func():
    data = {'key': [1, 2, 3]}
    assert data['key'][1] == 5
'''):
        with AssertImportHook():
            import test_complex
            try:
                test_complex.test_func()
                assert False, "Should have raised TestFailure"
            except TestFailure as e:
                # The error should contain useful debugging info
                assert e.value is not None


@suite.test
def multiple_assertions_in_function():
    """Test that multiple assertions in one function work correctly."""
    with temp_module('test_multiple', '''
from attest import assert_hook

def test_func():
    assert 1 == 1  # This should pass
    assert 2 == 2  # This should pass
    assert 3 == 4  # This should fail
'''):
        with AssertImportHook():
            import test_multiple
            try:
                test_multiple.test_func()
                assert False, "Should have raised TestFailure"
            except TestFailure:
                pass  # Expected


@suite.test
def empty_module():
    """Test that empty modules can be imported."""
    with temp_module('test_empty', ''):
        with AssertImportHook():
            import test_empty
            # Should not raise any errors


@suite.test
def module_with_syntax_error():
    """Test that modules with syntax errors raise ImportError."""
    with temp_module('test_syntax_error', '''
from attest import assert_hook

def test_func(
    # Missing closing parenthesis
'''):
        with AssertImportHook():
            try:
                import test_syntax_error
                assert False, "Should have raised exception"
            except (ImportError, SyntaxError):
                pass  # Expected


@suite.test
def assert_transformer_with_package():
    """Test AssertTransformer with package paths."""
    source = 'from attest import assert_hook\n'
    transformer = AssertTransformer(source, '<test>')
    module = transformer.make_module('test_pkg_path', newpath=['/tmp'])

    # Check that __path__ is set for packages
    assert hasattr(module, '__path__')
    assert module.__path__ == ['/tmp']

    # Clean up
    del sys.modules['test_pkg_path']


@suite.test
def hook_with_class_definitions():
    """Test that classes with assertions are rewritten correctly."""
    with temp_module('test_class', '''
from attest import assert_hook

class TestClass:
    def method(self):
        x = 10
        assert x == 10
        return x
'''):
        with AssertImportHook():
            import test_class
            obj = test_class.TestClass()
            result = obj.method()
            assert result == 10


@suite.test
def hook_preserves_globals_and_locals():
    """Test that assert_hook preserves globals and locals correctly."""
    with temp_module('test_scope', '''
from attest import assert_hook

global_var = "global"

def test_func():
    local_var = "local"
    assert global_var == "global"
    assert local_var == "local"
'''):
        with AssertImportHook():
            import test_scope
            test_scope.test_func()  # Should not raise


@suite.test
def reimport_after_modification():
    """Test that re-importing after disable/enable works."""
    with temp_module('test_reimport', '''
from attest import assert_hook
counter = 1
'''):
        # Use the hook directly, not as context manager
        # since we want to manipulate enable/disable manually
        AssertImportHook.enable()
        try:
            import test_reimport
            assert test_reimport.counter == 1

            # Disable hook
            AssertImportHook.disable()

            # Remove from sys.modules
            del sys.modules['test_reimport']

            # Re-enable
            AssertImportHook.enable()

            # Import again should work
            import test_reimport
            assert test_reimport.counter == 1
        finally:
            # Ensure hook is enabled for other tests
            AssertImportHook.enable()
