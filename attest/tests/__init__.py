from attest import Tests


suite = lambda mod: 'attest.tests.' + mod + '.suite'

all = Tests([suite('asserts'),
             suite('collections'),
             suite('classy'),
             suite('reporters'),
            ])
