from setuptools import setup


setup(
    name='Attest',
    version='0.1dev',
    description='Modern, Pythonic unit testing.',

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
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Testing',
    ]
)
