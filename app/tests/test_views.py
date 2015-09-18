from flask.ext.testing import TestCase

from app.factory import create_app
from app.models import User

from .test_models import DbTestCase

LOGGED_IN_SENTINEL = '<a href="/me"'

class ViewTestCase(DbTestCase):
    def create_app(self):
        config = self.BASE_APP_CONFIG.copy()
        config.update(
            DEBUG=False,
            WTF_CSRF_ENABLED=False,
            # This speeds tests up considerably.
            SECURITY_PASSWORD_HASH='plaintext',
            CACHE_NO_NULL_WARNING=True,
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

    def create_user(self, email, password):
        datastore = self.app.extensions['security'].datastore
        return datastore.create_user(email=email, password=password)

    def login(self, email=None, password=None):
        if email is None:
            email = u'test@example.org'
            password = 'test123'
            self.create_user(email=email, password=password)
        res = self.client.post('/login', data=dict(
            next='/',
            submit="Login",
            email=email,
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
        u = self.create_user(email=u'u@example.org', password='t')
        self.login('u@example.org', 't')
        self.assert200(self.client.get('/user/%d' % u.id))

    def test_my_profile_is_ok(self):
        self.login()
        self.assert200(self.client.get('/me'))

    def test_my_expertise_is_ok(self):
        self.login()
        self.assert200(self.client.get('/my-expertise'))

    def test_dashboard_is_ok(self):
        self.login()
        self.assert200(self.client.get('/dashboard'))

    def test_search_is_ok(self):
        self.login()
        self.assert200(self.client.get('/search'))

    def test_recent_users_is_ok(self):
        self.login()
        self.assert200(self.client.get('/users/recent'))

    def test_user_profiles_require_login(self):
        self.assertRedirects(self.client.get('/user/1234'),
                             '/login?next=%2Fuser%2F1234')
