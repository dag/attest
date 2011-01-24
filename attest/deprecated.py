import inspect
from contextlib import contextmanager

from . import statistics


class Loader(object):
    """Run tests with Attest via distribute.

    .. deprecated:: 0.5
        :meth:`~attest.reporters.AbstractReporter.test_loader` is preferred.

    """

    def loadTestsFromNames(self, names, module=None):
        mod, collection = names[0].rsplit('.', 1)
        mod = __import__(mod, fromlist=[collection])
        collection = getattr(mod, collection)
        collection.run()
        raise SystemExit


def assert_(expr, msg=None):
    """Like :keyword:`assert`, but counts the assertion.

    .. deprecated:: 0.5 :func:`~attest.eval.assert_hook` is preferred.

    """
    statistics.assertions += 1
    if not expr:
        if msg is None:
            raise AssertionError
        raise AssertionError(msg)
    return expr


class Assert(object):
    """Wrap an object such that boolean operations on it fails with an
    :exc:`AssertionError` if the operation results in :const:`False`,
    with more helpful error messages on failure than :keyword:`assert`.

    A test failure is simply an unhandled exception, so it is completely
    optional to use this class.

    Examples::

        Assert(1 + 1) == 2
        2 in Assert([1, 2, 3])

    Attributes are proxied to the wrapped object, returning the result
    wrapped as well::

        hello = Assert('hello')
        hello == 'hello'
        hello.upper() == 'HELLO'
        hello.capitalize() == 'Hello'

    Used in boolean context, fails if non-true. These all fail::

        bool(Assert(0))
        if Assert(0): pass
        assert Assert(0)

    Identical to, except for the more helpful failure message::

        Assert(bool(0)) == True

    If you pass more than one argument, the first is assumed to be a
    predicate callable to which the rest of the arguments are passed. These
    are identical::

        Assert.isinstance(0, int)
        Assert(isinstance, 0, int)

    .. deprecated:: 0.5 :func:`~attest.eval.assert_hook` is preferred.

    """

    #: The wrapped object
    obj = None

    def __init__(self, *args):
        if len(args) == 1:
            obj = args[0]
            if isinstance(obj, Assert):
                self.obj = obj.obj
            else:
                self.obj = obj
        elif len(args) > 1:
            args = list(args)
            predicate = args.pop(0)
            name = predicate.__name__
            arglist = ', '.join(map(_repr, args))
            self.obj = assert_(predicate(*args),
                               'not %s(%s)' % (name, arglist))

    @property
    def __class__(self):
        return Assert(self.obj.__class__)

    def __str__(self):
        """Wrapped proxy to the wrapped object's *__str__*, can be used for
        testing the string adaption of the object::

            Assert(1).__str__() == '1'

        .. warning:: :func:`str` on :class:`Assert` objects does not work.

        """
        return Assert(self.obj.__str__())

    def __getattr__(self, name):
        """Proxy all attributes to the wrapped object, wrapping the
        result.

        """
        return Assert(getattr(self.obj, name))

    def __call__(self, *args, **kwargs):
        """Allow calling of wrapped callables, wrapping the return value.
        Useful for testing methods on a wrapped object via attribute
        proxying::

            Assert('Hello').upper() == 'HELLO'

        """
        return Assert(self.obj(*args, **kwargs))

    def __getitem__(self, key):
        """Access an item on the wrapped object and return the result
        wrapped as well.

        ::

            Assert([1, 2, 3])[1] == 2

        """
        return Assert(self.obj[key])

    def __eq__(self, obj):
        """Test for equality with ``==``."""
        return assert_(self.obj == obj, '%r != %r' % (self.obj, obj))

    def __ne__(self, obj):
        """Test for inequality with ``!=``."""
        return assert_(self.obj != obj, '%r == %r' % (self.obj, obj))

    def is_(self, obj):
        """The :keyword:`is` operator is not overridable, for good reasons
        (that would defeat its purpose), so you can use this method for
        asserting identity::

            Assert(True).is_(True)

        .. versionchanged:: 0.3
            Checks the wrapped object for :class:`Assert` instances.

        """
        if isinstance(obj, Assert):
            obj = obj.obj
        return assert_(self.obj is obj, '%r is not %r' % (self.obj, obj))

    def is_not(self, obj):
        """The negated form of :meth:`is_`, corresponding to the ``is not``
        operation::

            Assert([]).is_not([])

        .. versionchanged:: 0.3
            Checks the wrapped object for :class:`Assert` instances.

        """
        if isinstance(obj, Assert):
            obj = obj.obj
        return assert_(self.obj is not obj, '%r is %r' % (self.obj, obj))

    def __contains__(self, obj):
        """Test for membership with :keyword:`in`."""
        return assert_(obj in self.obj, '%r not in %r' % (obj, self.obj))

    def in_(self, obj):
        """Assert membership. While you can use the :keyword:`in` operator,
        its order is inconsistent with the rest of the operators and doesn't
        work with the ``not in`` operation.

        ::

            2 in Assert([1, 2, 3])
            Assert(2).in_([1, 2, 3])

        """
        return assert_(self.obj in obj, '%r not in %r' % (self.obj, obj))

    def not_in(self, obj):
        """The negated form of :meth:`in_`, corresponding to the ``not in``
        operation::

            Assert(0).not_in([1, 2, 3])

        """
        return assert_(self.obj not in obj, '%r in %r' % (self.obj, obj))

    def __lt__(self, obj):
        """Test for lesserness with ``<``."""
        return assert_(self.obj < obj, '%r >= %r' % (self.obj, obj))

    def __le__(self, obj):
        """Test for lesserness or equality with ``<=``."""
        return assert_(self.obj <= obj, '%r > %r' % (self.obj, obj))

    def __gt__(self, obj):
        """Test for greaterness with ``>``."""
        return assert_(self.obj > obj, '%r <= %r' % (self.obj, obj))

    def __ge__(self, obj):
        """Test for greaterness or equality with ``>=``."""
        return assert_(self.obj >= obj, '%r < %r' % (self.obj, obj))

    def __nonzero__(self):
        """Test for truthiness in boolean context."""
        return bool(assert_(self.obj, 'not %r' % self.obj))

    @staticmethod
    @contextmanager
    def raises(*exceptions):
        """Context manager that fails if *none* of the `exceptions` are
        raised. Yields the captured exception as an :term:`assertive
        object`.

        ::

            with Assert.raises(IOError) as error:
                open('/etc/passwd', 'w')

            error.errno == 13

        :param exceptions: Expected exception classes.

        """
        statistics.assertions += 1
        proxy = Assert()
        try:
            yield proxy
        except exceptions, error:
            proxy.obj = error
        else:
            if len(exceptions) > 1:
                errors = '(' + ', '.join(e.__name__ for e in exceptions) + ')'
            else:
                errors = exceptions[0].__name__
            raise AssertionError("didn't raise %s" % errors)

    @staticmethod
    @contextmanager
    def not_raising(exception):
        """Context manager that fails if a particular exception is raised.
        A raised exception constitutes a failure anyway and this is mainly
        used for testing Attest itself.

        ::

            with Assert.not_raising(IOError):
                open('/etc/passwd', 'r')

        :param exception: An exception class.

        """
        statistics.assertions += 1
        try:
            yield
        except exception:
            raise AssertionError('raised %s' % exception.__name__)

    @staticmethod
    def isinstance(obj, classinfo):
        """Test that an object is an instance of a class or a :func:`tuple`
        of classes. Corresponds to :func:`.isinstance`.

        .. versionadded:: 0.4

        """
        if isinstance(obj, Assert):
            obj = obj.obj
        return assert_(isinstance(obj, classinfo),
                       'not isinstance(%r, %s)' % (obj, _repr(classinfo)))

    @staticmethod
    def not_isinstance(obj, classinfo):
        """Negated version of :meth:`isinstance`.

        .. versionadded:: 0.4

        """
        if isinstance(obj, Assert):
            obj = obj.obj
        return assert_(not isinstance(obj, classinfo),
                       'isinstance(%r, %s)' % (obj, _repr(classinfo)))

    @staticmethod
    def issubclass(obj, cls):
        """Test that `obj` is a subclass of `cls` or a subclass of a class
        inside `cls`. Corresponds to :func:`.issubclass`.

        .. versionadded:: 0.4

        """
        if isinstance(obj, Assert):
            obj = obj.obj
        return assert_(issubclass(obj, cls),
                       'not issubclass(%s, %s)' % (_repr(obj), _repr(cls)))

    @staticmethod
    def not_issubclass(obj, cls):
        """Negated version of :meth:`issubclass`.

        .. versionadded:: 0.4

        """
        if isinstance(obj, Assert):
            obj = obj.obj
        return assert_(not issubclass(obj, cls),
                       'issubclass(%s, %s)' % (_repr(obj), _repr(cls)))

    @property
    def json(self):
        """Parse the wrapped object as JSON. Requires Python 2.6 or the
        simplejson package.

        .. versionadded:: 0.4

        """
        try:
            import simplejson as json
        except ImportError:
            import json
        return Assert(json.loads(self.obj))

    def css(self, selector):
        """Parse the wrapped object as :abbr:`HTML
        (HyperText Markup Language)` and return an :term:`assertive
        <assertive object>` list of elements matching the :abbr:`CSS
        (Cascading Style Sheets)` `selector`.  Requires lxml 2.0 or newer.

        .. note::

            Not tested on Python 2.5 and PyPy due to difficulties
            installing lxml for these implementations.

        .. versionadded:: 0.4

        """
        from lxml import html
        return Assert(html.fromstring(self.obj).cssselect(selector))

    def xpath(self, path):
        """Parse the wrapped object as :abbr:`XML
        (eXtensible Markup Language)` and return an :term:`assertive
        <assertive object>` list of elements matching the :abbr:`XPath
        (XML Path Language)` *path*.  Requires lxml 2.0 or newer.

        .. note::

            Not tested on Python 2.5 and PyPy due to difficulties
            installing lxml for these implementations.

        .. versionadded:: 0.4

        """
        from lxml import etree
        return Assert(etree.fromstring(self.obj).xpath(path))

    def passed_to(self, func, *args, **kwargs):
        """Pass the unwrapped object to a function and return its result
        as an :term:`assertive object`.

        These are identical::

            Assert(len([1, 2, 3])) == 3
            Assert([1, 2, 3]).passed_to(len) == 3

        Mainly useful with Assert objects that comes from the outside, e.g.
        yielded from a context, from methods like :meth:`css` etc.

        .. versionadded:: 0.4

        """
        return Assert(func(self.obj, *args, **kwargs))

    def attr(self, name):
        """Safely get an attribute from the wrapped object.

        .. versionadded:: 0.4

        """
        return Assert(getattr(self.obj, name))

    def __repr__(self):
        """Not proxied to the wrapped object. To test that do something
        like::

            Assert(repr(obj)) == 'expectation'

        """
        return 'Assert(%r)' % self.obj


def _repr(obj):
    """Internal :func:`repr` that tries to be more close to original
    code.

    """
    if inspect.isclass(obj):
        return obj.__name__
    elif type(obj) is tuple:
        return '(%s)' % ', '.join(map(_repr, obj))
    return repr(obj)
