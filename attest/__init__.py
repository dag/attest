# coding:utf-8
import sys
from attest.eval import assert_hook, AssertImportHook

if sys.version_info[:2] > (2, 5) or hasattr(sys, 'pypy_version_info'):
    if not any(isinstance(ih, AssertImportHook) for ih in sys.meta_path):
        sys.meta_path.insert(0, AssertImportHook())

from attest import statistics
from attest.collectors import *
from attest.reporters import *
from attest.contexts import *
from attest.deprecated import *
