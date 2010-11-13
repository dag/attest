from __future__ import absolute_import

from attest import Tests

from .asserts import asserts
from .collections import collections
from .classy import classy

tests = Tests([asserts, collections, classy])
