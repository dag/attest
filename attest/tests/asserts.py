from __future__ import with_statement

from attest import Tests, Assert
import attest


suite = Tests()


@suite.test
def raises():
    """Assert.raises"""

    try:
        with Assert.raises(RuntimeError):
            pass
    except AssertionError, e:
        Assert(e).__str__() == "didn't raise RuntimeError"
    else:
        raise AssertionError("didn't fail for missing exception")

    # Groups of allowed exceptions
    try:
        with Assert.raises(RuntimeError, ValueError):
            pass
    except AssertionError, e:
        Assert(e).__str__() == "didn't raise (RuntimeError, ValueError)"
    else:
        raise AssertionError("didn't fail for missing exception")

    with Assert.raises(RuntimeError, ValueError) as error:
        raise RuntimeError
    error.__class__.is_(RuntimeError)

    with Assert.raises(RuntimeError, ValueError) as error:
        raise ValueError('invaluable')
    error.__class__.is_(ValueError)
    error.__str__() == 'invaluable'

    with Assert.raises(AssertionError):
        error.args == ('valuable',)


@suite.test
def not_raising():
    """Assert.not_raising"""

    with Assert.raises(AssertionError):
        with Assert.not_raising(RuntimeError):
            raise RuntimeError

    try:
        with Assert.not_raising(RuntimeError):
            pass
    except Exception:
        raise AssertionError('failed despite not raising RuntimeError')


@suite.test
def equality():
    """Assert() == and !="""

    Assert(1) == 1
    Assert(1) != 0

    with Assert.raises(AssertionError):
        Assert(1) == 0

    with Assert.raises(AssertionError):
        Assert(1) != 1


@suite.test
def compare():
    """Assert() comparisons"""

    Assert(1) > 0
    Assert(0) < 1
    Assert(1) >= 0
    Assert(1) >= 1
    Assert(0) <= 0
    Assert(0) <= 1

    with Assert.raises(AssertionError):
        Assert(0) > 1

    with Assert.raises(AssertionError):
        Assert(1) < 0

    with Assert.raises(AssertionError):
        Assert(0) >= 1

    with Assert.raises(AssertionError):
        Assert(0) >= 1

    with Assert.raises(AssertionError):
        Assert(1) <= 0

    with Assert.raises(AssertionError):
        Assert(1) <= 0


@suite.test
def contains():
    """Assert() membership"""

    1 in Assert([0,1,2])
    Assert(1).in_([0,1,2])
    Assert(3).not_in([0,1,2])

    with Assert.raises(AssertionError):
        3 in Assert([0,1,2])

    with Assert.raises(AssertionError):
        Assert(3).in_([0,1,2])

    with Assert.raises(AssertionError):
        Assert(1).not_in([0,1,2])


@suite.test
def identity():
    """Assert() object identity"""

    Assert(True).is_(True)
    Assert(False).is_not(True)
    Assert(True).is_(Assert(True))
    Assert(False).is_not(Assert(True))
    Assert([]).is_not([])

    with Assert.raises(AssertionError):
        Assert(False).is_(True)

    with Assert.raises(AssertionError):
        Assert(True).is_not(True)

    with Assert.raises(AssertionError):
        Assert(False).is_(Assert(True))

    with Assert.raises(AssertionError):
        Assert(True).is_not(Assert(True))

    with Assert.raises(AssertionError):
        Assert([]).is_([])


@suite.test
def proxy():
    """Assert().remote_attribute"""

    hello = Assert('hello')
    hello == 'hello'
    hello.upper() == 'HELLO'
    hello.attr('upper').attr('__name__') == 'upper'

    with Assert.raises(AssertionError):
        hello.upper() == 'hello'

    with Assert.raises(AssertionError):
        Assert(3).__str__() == '4'

    with Assert.raises(AssertionError):
        hello.attr('upper').attr('__name__') == 'lower'


@suite.test
def boolean():
    """Assert() in boolean context"""

    bool(Assert(1))

    with Assert.raises(AssertionError):
        bool(Assert(0))


@suite.test
def nested_assert():
    """Assert(Assert(var)) is Assert(var)"""

    Assert(Assert('hello')).__class__.is_(str)


@suite.test
def isinstance():
    """Assert.isinstance"""

    with Assert.raises(AssertionError) as error:
        Assert.isinstance('hello', (int, float))
    error.__str__() == "not isinstance('hello', (int, float))"

    with Assert.raises(AssertionError) as error:
        Assert.isinstance('hello', int)
    error.__str__() == "not isinstance('hello', int)"

    Assert.isinstance('hello', basestring)


@suite.test
def not_isinstance():
    """Assert.not_isinstance"""

    with Assert.raises(AssertionError) as error:
        Assert.not_isinstance(1, (int, float))
    error.__str__() == "isinstance(1, (int, float))"

    with Assert.raises(AssertionError) as error:
        Assert.not_isinstance(1, int)
    error.__str__() == "isinstance(1, int)"

    Assert.not_isinstance('hello', int)


@suite.test
def issubclass():
    """Assert.issubclass"""

    with Assert.raises(AssertionError) as error:
        Assert.issubclass(str, (int, float))
    error.__str__() == "not issubclass(str, (int, float))"

    with Assert.raises(AssertionError) as error:
        Assert.issubclass(str, int)
    error.__str__() == "not issubclass(str, int)"

    Assert.issubclass(str, str)


@suite.test
def not_issubclass():
    """Assert.not_issubclass"""

    with Assert.raises(AssertionError) as error:
        Assert.not_issubclass(int, (int, float))
    error.__str__() == "issubclass(int, (int, float))"

    with Assert.raises(AssertionError) as error:
        Assert.not_issubclass(int, int)
    error.__str__() == "issubclass(int, int)"

    Assert.not_issubclass(int, str)


@suite.test
def json():
    """Assert.json"""

    Assert('{"works": true}').json == dict(works=True)
    Assert('{"works": true}').json != dict(works=False)

    with Assert.raises(AssertionError):
        Assert('{"works": true}').json != dict(works=True)

    with Assert.raises(AssertionError):
        Assert('{"works": true}').json == dict(works=False)


try:
    import lxml
except ImportError:
    lxml = None

@suite.test_if(lxml)
def css():
    """Assert.css"""

    html = Assert("""
        <div id="maincontent">
            <div class="container">
                <p>Hello World</p>
            </div>
        </div>
    """)

    html.css('#maincontent .container p')[0].text == 'Hello World'

    with Assert.raises(AssertionError):
        html.css('#maincontent .container p')[0].text != 'Hello World'


@suite.test_if(lxml)
def xpath():
    """Assert.xpath"""

    xml = Assert("""
        <div id="maincontent">
            <div class="container">
                <p>Hello World</p>
            </div>
        </div>
    """)

    path = '/div[@id="maincontent"]/div[@class="container"]/p'
    xml.xpath(path)[0].text == 'Hello World'

    with Assert.raises(AssertionError):
        xml.xpath(path)[0].text != 'Hello World'


@suite.test
def passed_to():
    """Assert.passed_to"""

    Assert([1, 2, 3]).passed_to(len) == 3
    Assert(1).passed_to(str) == '1'
    Assert('a').passed_to(int, 16) == 10
    Assert('a').passed_to(int, base=16) == 10

    with Assert.raises(AssertionError):
        Assert([1, 2, 3]).passed_to(len) != 3

    with Assert.raises(AssertionError):
        Assert(1).passed_to(str) != '1'

    with Assert.raises(AssertionError):
        Assert('a').passed_to(int, 16) != 10

    with Assert.raises(AssertionError):
        Assert('a').passed_to(int, base=16) != 10


@suite.test
def predicate():
    with Assert.raises(AssertionError):
        Assert(bool, 0)
    Assert(bool, 1)
