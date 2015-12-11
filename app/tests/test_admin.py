from base64 import b64encode

from flask import Flask
from flask_testing import TestCase

from .test_views import ViewTestCase
from ..admin import _init_basic_auth as init_basic_auth

class AdminTestCase(ViewTestCase):
    BASE_APP_CONFIG = ViewTestCase.BASE_APP_CONFIG.copy()

    BASE_APP_CONFIG['ADMIN_UI_USERS'] = ['admin@example.org']

    def setUp(self):
        super(AdminTestCase, self).setUp()
        self.admin_user = self.create_user(u'admin@example.org', 'password')
        self.normal_user = self.create_user(u'normal@example.org', 'password')


class UserModelViewTests(AdminTestCase):
    def test_anonymous_users_are_redirected_to_login(self):
        self.assertRedirects(self.client.get('/admin/user/'),
                             '/login?next=%2Fadmin%2Fuser%2F')

    def test_non_admin_users_receive_403(self):
        self.login('normal@example.org', 'password')
        self.assert403(self.client.get('/admin/user/'))

    def test_admin_users_are_not_redirected_to_login(self):
        self.login('admin@example.org', 'password')
        self.assert200(self.client.get('/admin/user/'))


class StatsViewTests(AdminTestCase):
    def test_anonymous_users_are_redirected_to_login(self):
        self.assertRedirects(self.client.get('/admin/stats/'),
                             '/login?next=%2Fadmin%2Fstats%2F')

    def test_non_admin_users_receive_403(self):
        self.login('normal@example.org', 'password')
        self.assert403(self.client.get('/admin/stats/'))

    def test_admin_users_are_not_redirected_to_login(self):
        self.login('admin@example.org', 'password')
        self.assert200(self.client.get('/admin/stats/'))


class BasicAuthTests(TestCase):
    def create_app(self):
        app = Flask('test')
        app.config.update({'ADMIN_UI_BASIC_AUTH': 'foo:bar'})

        @app.route('/foo/bar')
        def non_admin_path():
            return "I am a non-admin path!"

        @app.route('/admin/blarg')
        def admin_path():
            return "I am an admin path!"

        init_basic_auth(app)
        return app

    def test_non_admin_paths_are_accessible(self):
        self.assert200(self.client.get('/foo/bar'))

    def test_admin_paths_receive_401(self):
        res = self.client.get('/admin/blarg')
        self.assert401(res)
        self.assertEqual(res.headers['WWW-Authenticate'],
                         'Basic realm="NoI Admin"')

    def test_admin_paths_with_invalid_userpass_receive_401(self):
        res = self.client.get('/admin/blarg', headers={
            'Authorization': 'Basic %s' % b64encode('foo:NOT BAR')
        })
        self.assert401(res)

    def test_admin_paths_with_valid_userpass_are_accessible(self):
        res = self.client.get('/admin/blarg', headers={
            'Authorization': 'Basic %s' % b64encode('foo:bar')
        })
        self.assert200(res)
