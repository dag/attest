Modern, Pythonic unit testing
=============================

Attest is a unit testing framework for Python emphasising modern idioms and
conventions.

::

    from attest import Tests
    math = Tests()

    @math.test
    def arithmetics():
        """Ensure that the laws of physics are in check."""
        assert 1 + 1 == 2

    if __name__ == '__main__':
        math.run()


Overview
--------

Why another testing framework and what sets it apart?

* *unittest* is overly complicated and its API makes more sense in Java
  than in Python. Attest has a simple API that makes it powerful and easy
  to use and feels just right for Python programmers.

* *nose* is on the right track but it still relies on naming conventions and
  implicit test discovery, and building on unittest means it retains its
  complexity. Attest takes *The Zen of Python* seriously and is completely
  explicit with no unpredictable magic.

* *py.test* is powerful but also the most magic of all options. This is not a
  concern for everyone, but if you prefer to be in control of your tools
  then Attest might be for you.

Attest…

* is not built on top of unittest or any other framework (but it is
  compatible with unittest) allowing it to rethink testing from the ground
  up.

* follows :pep:`8` and :pep:`20` and lets you do too.

* uses modern concepts such as context managers for fixtures and decorators
  for test registration.

* makes minimal assumptions so you can write your tests however you prefer.
