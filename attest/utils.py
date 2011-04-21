import sys
from array import array


def get_terminal_size(default=(80, 24)):
    """Try to get the size of the terminal as a tuple ``(width, height)``
    falling back on `default`.

    .. versionadded:: 0.6

    """
    try:
        import fcntl, termios
    except ImportError:
        return default
    ary = array('h', fcntl.ioctl(sys.stdin, termios.TIOCGWINSZ, chr(0) * 8))
    return ary[1], ary[0]
