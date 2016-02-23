from unittest import TestCase
import mock
import flask_testing
from flask import Flask

from ..discourse import sso, api

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
        app.config['DISCOURSE'] = dict(
            api_key='abcd',
            origin='http://discourse',
            sso_secret='hi',
        )
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
