from attest import Tests


suite = lambda mod: 'tests.' + mod + '.suite'

all = Tests([suite('asserts'),
             suite('collections'),
             suite('classy'),
            ])
