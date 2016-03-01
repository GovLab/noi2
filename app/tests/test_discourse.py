import urlparse
from unittest import TestCase
import mock
import flask_testing
from flask import Flask
from flask_security.signals import user_registered
from flask.ext.login import user_logged_out

from .test_views import ViewTestCase
from .test_models import DbTestCase
from ..models import User,  Event, db
from ..signals import user_changed_profile
from ..discourse import sso, api
from ..discourse.models import DiscourseTopicEvent

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

@mock.patch('app.discourse.api.post')
@mock.patch('app.discourse.sso.get_user_avatar_url')
class SyncUserTests(TestCase):
    def test_it_works(self, get_user_avatar_url, post):
        get_user_avatar_url.return_value = 'http://blarg/avatar.png'
        post.return_value.status_code = 200
        sso.sync_user(User(
            username='bop',
            first_name='John',
            last_name='Doe',
            email='boop@example.com',
            id=321
        ), avatar_force_update=True, secret='blarg')

        post.return_value.raise_for_status.assert_not_called()

        _, args, kwargs = post.mock_calls[0]
        self.assertEqual(args, ('/admin/users/sync_sso',))
        data = dict(urlparse.parse_qsl(kwargs['data']))

        payload = sso.unpack_and_verify_payload(data, secret='blarg')

        self.assertEqual(payload, {
            'avatar_url': 'http://blarg/avatar.png',
            'avatar_force_update': 'true',
            'email': 'boop@example.com',
            'external_id': '321',
            'name': 'John Doe',
            'nonce': 'does not matter',
            'username': 'bop'
        })

    def test_raises_error_if_status_is_not_ok(self, get_user_avatar_url,
                                              post):
        post.return_value.raise_for_status.side_effect = Exception('blam')

        with self.assertRaisesRegexp(Exception, 'blam'):
            sso.sync_user(User(username='bop', id=321), secret='hi')

class LogoutUserTests(TestCase):
    def test_returns_false_if_user_has_no_username(self):
        self.assertFalse(sso.logout_user(User()))

    @mock.patch('app.discourse.api.get')
    def test_returns_false_if_user_not_in_discourse(self, get):
        get.return_value.status_code = 404
        self.assertFalse(sso.logout_user(User(username='bop', id=321)))
        get.return_value.raise_for_status.assert_not_called()

    @mock.patch('app.discourse.api.get')
    def test_raises_error_if_getting_user_id_fails(self, get):
        get.return_value.status_code = 500
        get.return_value.raise_for_status.side_effect = Exception('boom')

        with self.assertRaisesRegexp(Exception, 'boom'):
            sso.logout_user(User(username='bop', id=321))

    @mock.patch('app.discourse.api.post')
    @mock.patch('app.discourse.api.get')
    def test_raises_error_if_logging_out_user_fails(self, get, post):
        get.return_value = mock.MagicMock(status_code=200)
        post.return_value = mock.MagicMock(status_code=500)
        post.return_value.raise_for_status.side_effect = Exception('blam')

        with self.assertRaisesRegexp(Exception, 'blam'):
            sso.logout_user(User(username='bop', id=321))
        get.return_value.raise_for_status.assert_not_called()

    @mock.patch('app.discourse.api.post')
    @mock.patch('app.discourse.api.get')
    def test_returns_true_if_user_logged_out(self, get, post):
        get.return_value.status_code = 200
        get.return_value.json.return_value = {'user': {'id': 999}}
        post.return_value.status_code = 200

        self.assertTrue(sso.logout_user(User(username='bop', id=321)))

        get.assert_called_once_with('/users/by-external/321.json')
        post.assert_called_once_with('/admin/users/999/log_out')
        get.return_value.raise_for_status.assert_not_called()
        post.return_value.raise_for_status.assert_not_called()

class DiscourseTopicEventTests(DbTestCase):
    BASE_APP_CONFIG = DbTestCase.BASE_APP_CONFIG.copy()

    BASE_APP_CONFIG.update(DISCOURSE=FAKE_DISCOURSE_CONFIG)

    def test_url_works(self):
        evt = DiscourseTopicEvent(discourse_id=5, slug='beep-boop')
        self.assertEqual(evt.url, 'http://discourse/t/beep-boop/5')

    def test_get_or_create_can_get_existing(self):
        evt = DiscourseTopicEvent(discourse_id=15)
        db.session.add(evt)
        db.session.commit()
        self.assertEqual(DiscourseTopicEvent._get_or_create(15), evt)

    def test_get_or_create_can_create_new(self):
        evt = DiscourseTopicEvent._get_or_create(5)
        self.assertEqual(evt.discourse_id, 5)

    def test_delete_all_deletes_parent_events(self):
        db.session.add(DiscourseTopicEvent())
        db.session.add(DiscourseTopicEvent())
        db.session.commit()

        self.assertEqual(db.session.query(Event).count(), 2)

        DiscourseTopicEvent.delete_all()

        self.assertEqual(db.session.query(Event).count(), 0)

    def test_parent_event_is_deleted(self):
        evt = DiscourseTopicEvent()

        db.session.add(evt)
        db.session.commit()

        self.assertEqual(db.session.query(Event).count(), 1)

        db.session.delete(evt)
        db.session.commit()

        self.assertEqual(db.session.query(Event).count(), 0)

class ViewTests(ViewTestCase):
    BASE_APP_CONFIG = ViewTestCase.BASE_APP_CONFIG.copy()

    BASE_APP_CONFIG.update(DISCOURSE=FAKE_DISCOURSE_CONFIG)

    def test_jinja_globals_are_set(self):
        jinja_globals = self.app.jinja_env.globals
        self.assertEqual(jinja_globals['DISCOURSE_ENABLED'], True)
        self.assertEqual(jinja_globals['discourse_url']('/hi'),
                         'http://discourse/hi')

    @mock.patch('app.discourse.sso.sync_user')
    def test_sync_user_called_when_user_changed_profile(self, sync_user):
        user = self.create_user('foo@example.com', 'passwd')
        user_changed_profile.send(self.app, user=user, avatar_changed=True)
        sync_user.assert_called_once_with(user, avatar_force_update=True)

    @mock.patch('app.discourse.sso.logout_user')
    def test_logout_user_called_when_user_logged_out(self, logout_user):
        user = self.create_user('foo@example.com', 'passwd')
        user_logged_out.send(self.app, user=user)
        logout_user.assert_called_once_with(user)

    @mock.patch('app.discourse.sso.sync_user')
    def test_sync_user_called_when_user_registered(self, sync_user):
        user = self.create_user('foo@example.com', 'passwd')
        user_registered.send(self.app, user=user, confirm_token='u')
        sync_user.assert_called_once_with(user)

    def test_discourse_sso_requires_login(self):
        self.assertRequiresLogin('/discourse/sso')

    def test_discourse_sso_rejects_invalid_payloads(self):
        self.login()
        payload = sso.pack_and_sign_payload({'nonce': '1'}, secret='bad')
        response = self.client.get('/discourse/sso', query_string=payload)

        self.assertEqual(response.status_code, 400)

    def assertStartsWith(self, text, prefix):
        if not text.startswith(prefix):
            raise AssertionError('Expected "%s" to start with "%s"' % (
                text, prefix
            ))

    @mock.patch('app.discourse.models.DiscourseTopicEvent.update')
    def test_webhook_works(self, update):
        response = self.client.post('/discourse/webhook/post_created')
        self.assert200(response)
        self.assertEqual(response.data, 'Thanks!')
        update.assert_called_once_with()

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
        payload = sso.unpack_and_verify_payload(query_dict)

        self.assertStartsWith(
            payload['avatar_url'],
             'http://localhost/static/img/nopic-avatars/nopic-avatar'
        )
        del payload['avatar_url']

        self.assertEqual(payload, {
            'email': 'boop@example.com',
            'external_id': str(user.id),
            'name': 'Boop Jones',
            'nonce': '1',
            'username': 'boopmaster'
        })
