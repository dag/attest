"""
Attest
======

Attest is a unit testing framework built from the ground up with idiomatic
Python in mind. Unlike others, it is not built on top of unittest though it
provides compatibility by creating TestSuites from Attest collections.

It has a functional API inspired by `Flask`_ and a class-based API that
mimics Python itself. The core avoids complicated assumptions leaving you
free to write tests however you prefer.

.. _Flask: http://pypi.python.org/pypi/Flask/

::

    from attest import Tests, Assert
    math = Tests()

    @math.test
    def arithmetics():
        Assert(1 + 1) == 2

    if __name__ == '__main__':
        math.run()

"""

from setuptools import setup


setup(
    name='Attest',
    version='0.3',
    description='Modern, Pythonic unit testing.',
    long_description=__doc__,

    author='Dag Odenhall',
    author_email='dag.odenhall@gmail.com',
    license='Simplified BSD',
    url='http://packages.python.org/Attest/',

    py_modules=['attest'],

    install_requires=[
        'progressbar',
        'pygments',
    ],

    test_loader='attest:Loader',
    test_suite='tests.tests',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Testing',
    ]
)
