import urlparse
from unittest import TestCase
import mock
import flask_testing
from flask import Flask

from .test_views import ViewTestCase
from ..discourse import sso, api

FAKE_DISCOURSE_CONFIG = dict(
    api_key='abcd',
    origin='http://discourse',
    sso_secret='hi',
)

class HmacSigningTests(TestCase):
    def test_packing_and_unpacking_work_with_valid_signature(self):
        signed = sso.pack_and_sign_payload({'hello': 'there'}, secret='foo')
        payload = sso.unpack_and_verify_payload(signed, secret='foo')
        self.assertEqual(payload['hello'], 'there')

    def test_invalid_signature_error_is_raised(self):
        signed = sso.pack_and_sign_payload({'hello': 'there'}, secret='foo')
        with self.assertRaises(sso.InvalidSignatureError):
            payload = sso.unpack_and_verify_payload(signed, secret='bar')

@mock.patch('requests.request')
class ApiTests(flask_testing.TestCase):
    def create_app(self):
        app = Flask('discourse_test')
        app.config['DISCOURSE'] = FAKE_DISCOURSE_CONFIG
        return app

    def test_request_passes_api_username(self, request):
        api.request('get', '/blah', username='gu')
        request.assert_called_once_with(
            'get',
            'http://discourse/blah',
            params=dict(api_key='abcd', api_username='gu'),
        )

    def test_request_merges_params(self, request):
        api.request('get', '/blah', params={'hi': 'there'})
        request.assert_called_once_with(
            'get',
            'http://discourse/blah',
            params=dict(api_key='abcd', api_username='system', hi='there'),
        )

    def test_get_passes_extra_kwargs(self, request):
        api.get('/boop', extra=1)
        request.assert_called_once_with(
            'get',
            'http://discourse/boop',
            params=dict(api_key='abcd', api_username='system'),
            extra=1
        )

    def test_post_passes_extra_kwargs(self, request):
        api.post('/boop', extra=1)
        request.assert_called_once_with(
            'post',
            'http://discourse/boop',
            params=dict(api_key='abcd', api_username='system'),
            extra=1
        )

class ViewTests(ViewTestCase):
    BASE_APP_CONFIG = ViewTestCase.BASE_APP_CONFIG.copy()

    BASE_APP_CONFIG.update(DISCOURSE=FAKE_DISCOURSE_CONFIG)

    def test_jinja_globals_are_set(self):
        jinja_globals = self.app.jinja_env.globals
        self.assertEqual(jinja_globals['DISCOURSE_ENABLED'], True)
        self.assertEqual(jinja_globals['discourse_url']('/hi'),
                         'http://discourse/hi')

    def test_discourse_sso_requires_login(self):
        self.assertRequiresLogin('/discourse/sso')

    def test_discourse_sso_rejects_invalid_payloads(self):
        self.login()
        payload = sso.pack_and_sign_payload({'nonce': '1'}, secret='bad')
        response = self.client.get('/discourse/sso', query_string=payload)

        self.assertEqual(response.status_code, 400)

    def test_discourse_sso_redirects_to_discourse(self):
        user = self.create_user(
            email='boop@example.com',
            password='passwd',
            username='boopmaster',
            first_name='Boop',
            last_name='Jones',
        )
        self.login('boop@example.com', 'passwd')

        payload = sso.pack_and_sign_payload({'nonce': '1'}, secret='hi')
        response = self.client.get('/discourse/sso', query_string=payload)

        self.assertEqual(response.status_code, 302)

        loc = urlparse.urlparse(response.headers['location'])

        self.assertEqual(loc.scheme, 'http')
        self.assertEqual(loc.netloc, 'discourse')
        self.assertEqual(loc.path, '/session/sso_login')

        query_dict = dict(urlparse.parse_qsl(loc.query))
        self.assertEqual(sso.unpack_and_verify_payload(query_dict), {
            'avatar_url': 'http://localhost/static/img/nopic-avatars/nopic-avatar9.jpg',
            'email': 'boop@example.com',
            'external_id': str(user.id),
            'name': 'Boop Jones',
            'nonce': '1',
            'username': 'boopmaster'
        })
