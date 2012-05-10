from attest import assert_hook

# There was a bug caused by using assert_hook in __init__.py and a relative
# import. This file is used to test that that bug no longer exists.
from . import foo
