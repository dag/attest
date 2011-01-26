from attest import Tests

all = Tests('.'.join((__name__, mod, 'suite'))
            for mod in ('asserts',
                        'collectors',
                        'classy',
                        'reporters',
                        'contexts',
                        'hook'))
