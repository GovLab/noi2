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

    @mock.patch.object(linkedin.linkedin, 'authorized_response',
                       return_value=None)
    def test_failed_callback_flashes_error(self, authorized_response):
        res = self.client.get('/linkedin/callback', follow_redirects=True)
        self.assert200(res)
        authorized_response.assert_called_once_with()
        assert "Connection with LinkedIn canceled" in res.data

    @mock.patch.object(linkedin.linkedin, 'authorized_response',
                       return_value={'something': True})
    def test_successful_callback_works(self, authorized_response):
        res = self.client.get('/linkedin/callback', follow_redirects=True)
        self.assert200(res)
        authorized_response.assert_called_once_with()
        assert "Connection to LinkedIn established" in res.data
