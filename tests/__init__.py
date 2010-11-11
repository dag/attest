from __future__ import absolute_import

from schluck import Tests

from .asserts import asserts

tests = Tests()
tests.register(asserts)
