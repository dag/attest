.. currentmodule:: attest

Changelog
=========


0.4
---
:Release date: 2011-01-08

* Support for Python 3.1 and PyPy (besides existing support for 2.5-2.7).
* Reporters are now loaded via setuptools entry points, allowing
  third-party packages to register themselves automatically. The
  :func:`get_all_reporters` function was added to complement this
  extensibility.
* :class:`TestResult` was introduced and is now passed to reporters instead
  of the more limited set of arguments that were previously passed. This
  change is not backwards-compatible if you have custom reporters.
* Conditional test registration: :meth:`Tests.test_if`,
  :meth:`Tests.register_if`, :func:`test_if`.
* Many new :class:`Assert` methods:

  * :meth:`~Assert.isinstance` and :meth:`~Assert.not_isinstance`
  * :meth:`~Assert.issubclass` and :meth:`~Assert.not_issubclass`
  * :meth:`~Assert.json`, :meth:`~Assert.css` and :meth:`~Assert.xpath`
  * :meth:`~Assert.attr` and :meth:`~Assert.passed_to`
* Import fallbacks can be tested using :func:`disable_imports`.
* The :class:`Tests` constructor now accepts an iterable of contexts.
* Passing :class:`Assert` objects to the Assert constructor no-longer wraps
  multiple levels.
* Test names now include the class name for class-based test.
* Test registration via dotted name now handles unicode.


0.3
---
:Release date: 2010-11-27

* :const:`None` if yielded from a context is no-longer passed as arguments
  to tests.
* :meth:`Assert.is_` and :meth:`Assert.is_not`, if passed an
  :class:`Assert` instance, will unwrap it and test against the original
  object.


0.2
---
:Release date: 2010-11-26

* Functional tests can now have multiple contexts.
* Tests can be registered by dotted name (import path as string).
* Collections have a command-line interface via :meth:`Tests.main`.


0.1
---
:Release date: 2010-11-25
