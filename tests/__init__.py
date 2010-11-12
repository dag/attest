from __future__ import absolute_import

from schluck import Tests

from .asserts import asserts
from .collections import collections

tests = Tests([asserts, collections])
