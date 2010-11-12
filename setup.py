from setuptools import setup


setup(
    name='Schluck',
    version='0.1dev',
    description='Modern, Pythonic unit testing.',

    author='Dag Odenhall',
    author_email='dag.odenhall@gmail.com',
    license='Simplified BSD',
    url='http://dag.github.com/schluck/',

    py_modules=['schluck'],

    install_requires=[
        'progressbar',
        'pygments',
    ],

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
