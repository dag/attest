from attest import Tests, assert_hook

samples = Tests()

@samples.test
def number_and_sequence():
    number = 2 + 3
    sequence = [1, 2, 3]
    assert number in sequence and isinstance(number, float)

if __name__ == '__main__':
    samples.main()
