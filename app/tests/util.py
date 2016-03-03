import logging
from flask import Flask

from app import factory

def add_logging_to_app(app):
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)

    return app

def create_app(*args, **kwargs):
    app = factory.create_app(*args, **kwargs)
    return add_logging_to_app(app)

def create_empty_flask_app(name='app'):
    return add_logging_to_app(Flask(name))

# Taken from nose:
#
# https://github.com/nose-devs/nose/blob/master/nose/tools/trivial.py

def eq_(a, b, msg=None):
    """Shorthand for 'assert a == b, "%r != %r" % (a, b)
    """
    if not a == b:
        raise AssertionError(msg or "%r != %r" % (a, b))

