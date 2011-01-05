.. raw:: html

    <a href="https://github.com/dag/attest">
        <img style="position: fixed; top: 0; right: 0; border: 0;"
             src="https://assets1.github.com/img/30f550e0d38ceb6ef5b81500c64d970b7fb0f028?repo=&url=http%3A%2F%2Fs3.amazonaws.com%2Fgithub%2Fribbons%2Fforkme_right_orange_ff7600.png&path="
             alt="Fork me on GitHub" />
    </a>


Modern, Pythonic unit testing
=============================

.. container:: dictionary-entry

    **at·test** */əˈtɛst/*
        To affirm to be correct, true, or genuine.


The Why
-------

I'm not satisfied with the existing testing solutions.

* The standard unittest library is overly complicated and its API
  doesn't make sense for the problem it tries to solve. Classes are great
  for inheritance and multiple instances but tests are merely collections
  of callbacks. The use of camel case mixes badly with the code I'm testing
  which always follows :pep:`8`.

* Nose has the right idea with the ``@istest`` decorator but as it's not
  actually collecting marked tests it has to discover them all, which means
  you need a global namespace of tests if you're going flat. Test discovery
  relies on naming conventions and doesn't really adhere to the idiom that
  "explicit is better than implicit". Setup and teardown of flat tests
  doesn't ensure isolation.

* Admittedly I haven't tried py.test, but when I look at it I just see a big
  mess of metaprogrammatic string-programming magic. Not my cup of tea.

In my mind, tests are:

* Applications. I want to write my tests like I write application code.
* Collections of callables that fail if they raise unhandled exceptions.

*The Zen of Python* applies to testing just as well as to any other code.


The How
-------

*Attest* provides two styles for writing tests, one functional and one
object-oriented. The functional API is inspired by that of `Flask`_, not
for bandwagony reasons, but because it's a well-fit pattern for the problem
of "collections of callables". The object-oriented style follows standard
Python idioms for writing classes. It's easy to invent your own style
because Attest only assumes that a test is a callable and a collection an
iterable. There is no magic you have to account for - Attest is a library
for writing tests rather than a scriptable program for running tests. It's
up to you to organize and collect tests, though Attest will assist you.

Assertions are done with operator overloading; while I'm not usually too fond
of :abbr:`DSLs (Domain Specific Languages)`, I also find it difficult to
remember all the unittest assertion methods. Using the actual operators help.

::

    from attest import Tests, Assert

    math = Tests()

    @math.test
    def arithmetics():
        """Ensure that the laws of physics are in check."""
        Assert(1 + 1) == 2

    math.run()


The Rest
--------

.. toctree::
   :maxdepth: 2

   guide
   api
   Source code and issue tracking at GitHub <https://github.com/dag/attest/>


The Terms
---------

| Copyright © 2010, `Dag Odenhall <dag.odenhall@gmail.com>`_
| All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

.. container:: small-caps

    This software is provided by the copyright holders and contributors "as
    is" and any express or implied warranties, including, but not limited
    to, the implied warranties of merchantability and fitness for a
    particular purpose are disclaimed. In no event shall the copyright
    holder or contributors be liable for any direct, indirect, incidental,
    special, exemplary, or consequential damages (including, but not
    limited to, procurement of substitute goods or services; loss of use,
    data, or profits; or business interruption) however caused and on any
    theory of liability, whether in contract, strict liability, or tort
    (including negligence or otherwise) arising in any way out of the use
    of this software, even if advised of the possibility of such damage.


The Authors
-----------

.. include:: ../AUTHORS

.. _Flask: http://flask.pocoo.org/
