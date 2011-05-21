Quickstart
==========

So, you got Attest :doc:`installed </install>`? Great! Let's get started
writing tests!


The PyPI Metadata Module
------------------------

The `Python Package Index`_ exposes metadata for projects as :abbr:`JSON
(JavaScript Object Notation)`. Let's write a simple module to read this
data and test it with Attest!

.. _Python Package Index:
    http://pypi.python.org/pypi

The first order of business is to design the API we want. A good way to do
this is to draft the documentation first - this is dubbed `Readme Driven
Development`_ and goes well in hand with test driven development.

.. _Readme Driven Development:
    http://tom.preston-werner.com/2010/08/23/readme-driven-development.html

Suppose we came up with an API like this:

.. testsetup::

    import json
    import urllib2

    class Package(object):

        def __init__(self, name):
            url = 'http://pypi.python.org/pypi/%s/json' % name
            data = urllib2.urlopen(url).read()
            vars(self).update(json.loads(data)['info'])

>>> package = Package('Attest')
>>> package.author
u'Dag Odenhall'
>>> package.summary
u'Modern, Pythonic unit testing.'

Now we want to write the tests. It's a good idea to do this before we write
any actual code for the module itself because the tests lets us verify that
the eventual code does what we want and we can avoid manual testing.

Here's the API defined as tests::

    from attest import Tests
    from pypilib import Package  # our fictional module

    pypi = Tests()

    @pypi.test
    def properties():
        package = Package('Attest')
        assert package.author == 'Dag Odenhall'
        assert package.summary == 'Modern, Pythonic unit testing.'

    if __name__ == '__main__':
        pypi.run()

Save it as :file:`tests.py` and run it. What happens?

.. sourcecode:: console

    $ python tests.py
    Traceback (most recent call last):
      File "tests.py", line 2, in <module>
        from pypilib import Package  # our fictional module
    ImportError: No module named pypilib

As expected we get an :exc:`ImportError` because we haven't created our
module yet. So that's the next step! First we just stub the class::

    class Package(object):
        pass

This should fail because this constructor doesn't take any arguments. Let's
confirm this:

.. sourcecode:: pytb

    $ python tests.py
    [100%] 1 of 1 Time: 0:00:00

    properties
    ─────────────────────────────────────────────────────────────────────
    Traceback (most recent call last):
      File "tests.py", line 8, in properties
        package = Package('Attest')
    TypeError: object.__new__() takes no parameters

    Failures: 1/1 (0 assertions)

Just as expected. OK - so we write a custom constructor::

    class Package(object):
        def __init__(self, name):
            pass

Still fails:

.. sourcecode:: pytb

    Traceback (most recent call last):
      File "tests.py", line 9, in properties
        assert package.author == 'Dag Odenhall'
    AttributeError: 'Package' object has no attribute 'author'

It's time to write some real code! Here's our working module::

    import json
    import urllib2

    class Package(object):

        def __init__(self, name):
            url = 'http://pypi.python.org/pypi/%s/json' % name
            data = json.loads(urllib2.urlopen(url).read())
            self.author = data['info']['author']
            self.summary = data['info']['summary']

Now the tests pass:

.. sourcecode:: console

    $ python tests.py
    [100%] 1 of 1 Time: 0:00:00

    Failures: 0/1 (0 assertions)
