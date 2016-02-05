import datetime
import mock

from .. import linkedin
from  .test_views import ViewTestCase

class LinkedInDisabledTests(ViewTestCase):
    def test_linkedin_is_disabled_if_setting_not_present(self):
        self.assertTrue('LINKEDIN_ENABLED' not in self.app.jinja_env.globals)

    def test_authorize_is_404(self):
        res = self.client.get('/linkedin/authorize')
        self.assert404(res)

class LinkedInTests(ViewTestCase):
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

    def test_successful_callback_works(self):
        res = self.get_callback(fake_response={
            'access_token': 'blorp',
            'expires_in': 10000
        })
        self.assert200(res)

        user = self.last_created_user
        self.assertEqual(user.linkedin.access_token, 'blorp')
        self.assertAlmostEqual(user.linkedin.expires_in.total_seconds(),
                               10000, delta=120)

        assert "Connection to LinkedIn established" in res.data

    def test_authorize_requires_login(self):
        self.assertRequiresLogin('/linkedin/authorize')

    def test_callback_requires_login(self):
        self.assertRequiresLogin('/linkedin/callback')
