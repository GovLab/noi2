from flask.ext.testing import TestCase

from app.factory import create_app
from app.models import User

from .test_models import DbTestCase

LOGGED_IN_SENTINEL = '<a href="/me"'

class ViewTestCase(DbTestCase):
    def create_app(self):
        config = self.BASE_APP_CONFIG.copy()
        config.update(
            WTF_CSRF_ENABLED=False,
            SECURITY_REGISTERABLE=True,
            SECURITY_SEND_REGISTER_EMAIL=False,
            CACHE_NO_NULL_WARNING=True,
            SECRET_KEY='test',
            S3_BUCKET_NAME='test_bucket'
        )
        return create_app(config=config)

    def register_and_login(self, username, password):
        res = self.client.post('/register', data=dict(
            next='/',
            email=username,
            password=password,
            password_confirm=password,
            submit='Register'
        ), follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL in res.data
        return res

    def logout(self):
        res = self.client.get('/logout', follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL not in res.data
        return res

    def login(self, username, password):
        res = self.client.post('/login', data=dict(
            next='/',
            submit="Login",
            email=username,
            password=password
        ), follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL in res.data
        return res

class ViewTests(ViewTestCase):
    def test_main_page_is_ok(self):
        self.assert200(self.client.get('/'))

    def test_about_page_is_ok(self):
        self.assert200(self.client.get('/about'))

    def test_feedback_page_is_ok(self):
        self.assert200(self.client.get('/feedback'))

    def test_nonexistent_page_is_not_found(self):
        self.assert404(self.client.get('/nonexistent'))

    def test_registration_works(self):
        self.register_and_login('foo@example.org', 'test123')
        self.logout()
        self.login('foo@example.org', 'test123')

    def test_existing_user_profile_is_ok(self):
        self.register_and_login('foo@example.org', 'test123')
        user = User.query_in_deployment().filter_by(email='foo@example.org')
        self.assert200(self.client.get('/user/%d' % user.one().id))

    def test_user_profiles_require_login(self):
        self.assertRedirects(self.client.get('/user/1234'),
                             '/login?next=%2Fuser%2F1234')
