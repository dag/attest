Installation
============

Attest is verified to work on Python 2.5, 2.6, 2.7, 3.1 and PyPy. Because
of high reliance on context managers and decorators, it does not make much
sense to try and port it to any earlier version of Python.

Install as usual with *pip* or *easy_install*::

    easy_install Attest

This will also pull the two dependencies (progressbar and pygments) used
for producing fancy test reports on the command line. These are actually
optional, and if you prefer you can install Attest without them::

    easy_install -N Attest

If you want to use the convenience methods for testing HTML and XML, you
also need to have lxml installed which by default is not pulled as a
dependency. It's usually easiest to install it with your package manager,
if you're on Linux or similar; example for Ubuntu::

    sudo apt-get install python-lxml
