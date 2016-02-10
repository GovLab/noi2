# Taken from nose:
#
# https://github.com/nose-devs/nose/blob/master/nose/tools/trivial.py

def eq_(a, b, msg=None):
    """Shorthand for 'assert a == b, "%r != %r" % (a, b)
    """
    if not a == b:
        raise AssertionError(msg or "%r != %r" % (a, b))
