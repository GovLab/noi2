from .test_views import ViewTestCase

CSP_HEADER = 'Content-Security-Policy-Report-Only'

class ContentSecurityPolicyTests(ViewTestCase):
    def test_header_is_on_flask_security_endpoints(self):
        resp = self.client.get('/login')
        assert CSP_HEADER in resp.headers

    def test_header_is_on_homepage(self):
        resp = self.client.get('/')
        assert CSP_HEADER in resp.headers

    def test_report_endpoint_is_ok(self):
        resp = self.client.post('/csp-report')
        self.assertEqual('CSP violation reported.', resp.data)
        self.assert200(resp)
