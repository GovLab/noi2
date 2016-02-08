import datetime
import mock
import datetime
from unittest import TestCase
from flask_oauthlib.client import OAuthException

from .. import linkedin
from ..models import User, db, UserLinkedinInfo
from .test_models import DbTestCase
from .test_views import ViewTestCase

FAKE_AUTHORIZED_RESPONSE = {
    'access_token': 'blorp',
    'expires_in': 10000
}

FAR_IN_THE_PAST = datetime.datetime.now() - datetime.timedelta(days=50)
FAR_IN_THE_FUTURE = datetime.datetime.now() + datetime.timedelta(days=50)

class LinkedinDisabledTests(ViewTestCase):
    def test_linkedin_is_disabled_if_setting_not_present(self):
        self.assertTrue('LINKEDIN_ENABLED' not in self.app.jinja_env.globals)

    def test_authorize_is_404(self):
        res = self.client.get('/linkedin/authorize')
        self.assert404(res)

class UserLinkedinInfoTests(TestCase):
    def test_get_user_info_raises_exception_if_no_access_token(self):
        user = User(email='foo@bar')
        with self.assertRaisesRegexp(OAuthException,
                                     'Access token unavailable or expired'):
            linkedin.get_user_info(user)

    def test_get_user_info_raises_exception_if_token_is_invalid(self):
        info = UserLinkedinInfo(access_token='b',
                                access_token_expiry=FAR_IN_THE_FUTURE)
        user = User(linkedin=info)
        with self.assertRaisesRegexp(OAuthException,
                                     'Server returned HTTP 401.*blah'):
            mock_response = mock.Mock(status=401, data={'blah': 1})
            with mock.patch.object(linkedin.linkedin, 'get',
                                   return_value=mock_response):
                linkedin.get_user_info(user)

    def test_retrieve_access_token_is_none_if_linkedin_is_none(self):
        user = User()
        self.assertEqual(linkedin.retrieve_access_token(user), None)

    def test_retrieve_access_token_is_none_if_token_is_expired(self):
        info = UserLinkedinInfo(access_token='b',
                                access_token_expiry=FAR_IN_THE_PAST)
        user = User(linkedin=info)
        self.assertEqual(linkedin.retrieve_access_token(user), None)

    def test_retrieve_access_token_works(self):
        info = UserLinkedinInfo(access_token='b',
                                access_token_expiry=FAR_IN_THE_FUTURE)
        user = User(linkedin=info)
        self.assertEqual(linkedin.retrieve_access_token(user), ('b', ''))

    def test_profile_url_is_none_if_not_available(self):
        info = UserLinkedinInfo()
        self.assertEqual(info.profile_url, None)

    def test_profile_url_works(self):
        info = UserLinkedinInfo(user_info={'publicProfileUrl': 'http://u'})
        self.assertEqual(info.profile_url, 'http://u')

    def test_picture_url_is_high_res_if_available(self):
        info = UserLinkedinInfo(user_info={
            'pictureUrls': {
                'values': ['http://a', 'http://b']
            },
            'pictureUrl': 'http://c'
        })
        self.assertEqual(info.picture_url, 'http://a')

    def test_picture_url_falls_back_to_low_res(self):
        info = UserLinkedinInfo(user_info={'pictureUrl': 'http://c'})
        self.assertEqual(info.picture_url, 'http://c')

    def test_picture_url_is_none_if_not_available(self):
        info = UserLinkedinInfo()
        self.assertEqual(info.picture_url, None)

class LinkedinDbTests(DbTestCase):
    def setUp(self):
        super(LinkedinDbTests, self).setUp()
        self.user = User(email=u'a@example.org', password='a', active=True)
        db.session.add(self.user)
        db.session.commit()

    def test_linkedin_is_deleted_with_user(self):
        linkedin.store_access_token(self.user, FAKE_AUTHORIZED_RESPONSE)
        self.assertEqual(UserLinkedinInfo.query.count(), 1)
        db.session.delete(self.user)
        db.session.commit()
        self.assertEqual(UserLinkedinInfo.query.count(), 0)

    def test_only_one_linkedin_per_user_is_created(self):
        self.assertEqual(UserLinkedinInfo.query.count(), 0)
        linkedin.store_access_token(self.user, FAKE_AUTHORIZED_RESPONSE)
        linkedin.store_access_token(self.user, FAKE_AUTHORIZED_RESPONSE)
        self.assertEqual(UserLinkedinInfo.query.count(), 1)

    def test_headline_is_imported_from_profile(self):
        linkedin.update_user_fields_from_profile(self.user, {
            u'headline': 'Awesome Person'
        })
        self.assertEqual(self.user.position, 'Awesome Person')

    def test_unrecognized_country_name_in_profile_is_ignored(self):
        linkedin.update_user_fields_from_profile(self.user, {
            u'location': {u'country': {u'code': u'lolol'}},
        })
        self.assertEqual(self.user.country, None)

    def test_location_is_imported_from_profile(self):
        linkedin.update_user_fields_from_profile(self.user, {
            u'location': {u'country': {u'code': u'us'},
            u'name': u'Greater New York City Area'},
        })
        self.assertEqual(self.user.city, 'Greater New York City Area')
        self.assertEqual(self.user.country, 'US')

class LinkedinViewTests(ViewTestCase):
    BASE_APP_CONFIG = ViewTestCase.BASE_APP_CONFIG.copy()

    BASE_APP_CONFIG['LINKEDIN'] = dict(
        consumer_key='ckey',
        consumer_secret='csecret',
    )

    def test_linkedin_is_enabled_if_setting_present(self):
        self.assertTrue(self.app.jinja_env.globals['LINKEDIN_ENABLED'])

    @mock.patch.object(linkedin, 'gen_salt', return_value='boop')
    def test_authorize_redirects_to_linkedin(self, gen_salt):
        self.login()
        res = self.client.get('/linkedin/authorize')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res.headers['location'],
            'https://www.linkedin.com/uas/oauth2/authorization?'
            'response_type=code&client_id=ckey&'
            'redirect_uri=http%3A%2F%2Flocalhost%2Flinkedin%2Fcallback&'
            'scope=r_basicprofile&state=boop'
        )
        gen_salt.assert_called_with(10)

    def get_callback(self, fake_response):
        self.login()
        with self.client.session_transaction() as sess:
            sess['linkedin_state'] = 'b'
        with mock.patch.object(
            linkedin.linkedin, 'authorized_response',
            return_value=fake_response
        ) as authorized_response:
            res = self.client.get('/linkedin/callback?state=b',
                                  follow_redirects=True)
            authorized_response.assert_called_once_with()
            return res

    def test_callback_with_mismatched_state_fails(self):
        self.login()
        with self.client.session_transaction() as sess:
            sess['linkedin_state'] = 'hi'
        res = self.client.get('/linkedin/callback?state=blorp')
        self.assertEqual(res.data, 'Invalid state')

    def test_callback_with_no_session_state_fails(self):
        self.login()
        res = self.client.get('/linkedin/callback?state=blorp')
        self.assertEqual(res.data, 'Invalid state')

    def test_callback_with_no_state_fails(self):
        self.login()
        res = self.client.get('/linkedin/callback')
        self.assertEqual(res.data, 'Invalid state')

    def test_failed_callback_flashes_error(self):
        res = self.get_callback(fake_response=None)
        self.assert200(res)
        assert "Connection with LinkedIn canceled" in res.data

    @mock.patch.object(linkedin, 'update_user_info')
    def test_successful_callback_works(self, update_user_info):
        res = self.get_callback(fake_response=FAKE_AUTHORIZED_RESPONSE)
        self.assert200(res)

        user = self.last_created_user
        self.assertEqual(user.linkedin.access_token, 'blorp')
        self.assertAlmostEqual(user.linkedin.expires_in.total_seconds(),
                               10000, delta=120)
        assert update_user_info.called

        assert "Connection to LinkedIn established" in res.data

    def test_deauthorize_works(self):
        self.login()
        linkedin.store_access_token(self.last_created_user,
                                    FAKE_AUTHORIZED_RESPONSE)
        res = self.client.get('/linkedin/deauthorize')
        self.assertRedirects(res, '/me')
        self.assertEqual(self.last_created_user.linkedin, None)

    def test_deauthorize_requires_login(self):
        self.assertRequiresLogin('/linkedin/deauthorize')

    def test_authorize_requires_login(self):
        self.assertRequiresLogin('/linkedin/authorize')

    def test_callback_requires_login(self):
        self.assertRequiresLogin('/linkedin/callback')

    def test_connect_to_linkedin_is_shown_in_edit_profile(self):
        self.login()
        res = self.client.get('/me')
        self.assert200(res)

        assert 'href="/linkedin/authorize"' in res.data
        assert 'href="/linkedin/deauthorize"' not in res.data

    def test_disconnect_from_linkedin_is_shown_in_edit_profile(self):
        self.login()
        linkedin.store_access_token(self.last_created_user,
                                    FAKE_AUTHORIZED_RESPONSE)
        res = self.client.get('/me')
        self.assert200(res)

        assert 'href="/linkedin/authorize"' not in res.data
        assert 'href="/linkedin/deauthorize"' in res.data

    def test_linkedin_profile_url_is_shown_in_public_profile(self):
        self.login()
        linkedin.store_access_token(self.last_created_user,
                                    FAKE_AUTHORIZED_RESPONSE)
        self.last_created_user.linkedin.user_info = {
            'publicProfileUrl': 'http://linkedin.com/blarg'
        }
        res = self.client.get('/user/%d' % self.last_created_user.id)
        self.assert200(res)

        assert 'href="http://linkedin.com/blarg"' in res.data
        assert 'LinkedIn' in res.data

    def test_linkedin_is_not_shown_in_public_profile(self):
        self.login()
        res = self.client.get('/user/%d' % self.last_created_user.id)
        self.assert200(res)

        assert 'LinkedIn' not in res.data
