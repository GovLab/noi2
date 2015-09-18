from flask.ext.testing import TestCase

from app.factory import create_app
from app.models import db

LOGGED_IN_SENTINEL = '<a href="/me"'

class ViewTestCase(TestCase):
    def create_app(self):
        return create_app(config=dict(
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI='sqlite://',
            SECURITY_REGISTERABLE=True,
            SECURITY_SEND_REGISTER_EMAIL=False,
            NOI_DEPLOY='_default',
            CACHE_NO_NULL_WARNING=True,
            SECRET_KEY='test',
            S3_BUCKET_NAME='test_bucket'
        ))

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

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

    def test_user_profiles_require_login(self):
        self.assertRedirects(self.client.get('/user/1234'),
                             '/login?next=%2Fuser%2F1234')
