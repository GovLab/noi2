from flask import Flask
from flask.ext.testing import TestCase
from nose.tools import eq_

from .. import models

db = models.db

class DbTestCase(TestCase):
    BASE_APP_CONFIG = dict(
        # TODO: We should use a test postgres db instead, since it's
        # closer to our production deployment.
        SQLALCHEMY_DATABASE_URI='sqlite://',
        NOI_DEPLOY='_default'
    )

    def create_app(self):
        app = Flask('test')
        app.config.update(self.BASE_APP_CONFIG)
        db.init_app(app)
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

class UserDbTests(DbTestCase):
    def test_ensure_deployment_has_a_default_setting(self):
        u = models.User(email=u'a@example.org', password='a', active=True)
        db.session.add(u)
        db.session.commit()
        eq_(u.deployment, '_default')

def test_users_only_display_in_search_if_they_have_first_and_last_name():
    user = models.User()
    eq_(user.display_in_search, False)
    user.first_name = "John"
    eq_(user.display_in_search, False)
    user.last_name = "Doe"
    eq_(user.display_in_search, True)
