from __future__ import with_statement

import sys

from attest import Tests, Assert
import attest


suite = Tests()


@suite.test
def get_all_reporters():
    reporters = set(['auto', 'fancy', 'plain', 'xml'])
    Assert(set(attest.get_all_reporters())) == reporters


@suite.test
def get_reporter_by_name():
    reporters = dict(auto=attest.auto_reporter,
                     fancy=attest.FancyReporter,
                     plain=attest.PlainReporter,
                     xml=attest.XmlReporter,
                    )
    for name, reporter in reporters.iteritems():
        Assert(attest.get_reporter_by_name(name)) == reporter


@suite.test
def auto_reporter():
    # Inside tests, sys.stdout is not a tty
    Assert.isinstance(attest.auto_reporter(), attest.PlainReporter)

    sys.stdout, orig = sys.__stdout__, sys.stdout
    try:
        Assert.isinstance(attest.auto_reporter(), attest.FancyReporter)
        with attest.disable_imports('progressbar', 'pygments'):
            Assert.isinstance(attest.auto_reporter(), attest.PlainReporter)
    finally:
        sys.stdout = orig
