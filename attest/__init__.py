# coding:utf-8
import sys
from attest.eval import assert_hook, AssertImportHook

if not any(isinstance(ih, AssertImportHook) for ih in sys.meta_path):
    sys.meta_path.insert(0, AssertImportHook())

from attest import statistics
from attest.collectors import *
from attest.reporters import *
from attest.contexts import *
from attest.deprecated import *
