from attest import Tests, Assert
import attest


suite = Tests()


@suite.test
def get_all_reporters():
    reporters = set(['auto', 'fancy', 'plain', 'xml'])
    Assert(set(attest.get_all_reporters())) == reporters
