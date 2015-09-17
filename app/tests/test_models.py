from flask import Flask
from flask.ext.testing import TestCase
from nose.tools import eq_

from .. import models

db = models.db

class DbTest(TestCase):
    def create_app(self):
        app = Flask('test')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['NOI_DEPLOY'] = '_default'
        db.init_app(app)
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

class UserDbTests(DbTest):
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
