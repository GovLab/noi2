from flask.ext.testing import TestCase

from app.factory import create_app

class ViewTestCase(TestCase):
    def create_app(self):
        return create_app(config=dict(
            NOI_DEPLOY='_default',
            CACHE_NO_NULL_WARNING=True,
            SECRET_KEY='test',
            S3_BUCKET_NAME='test_bucket'
        ))

class ViewTests(ViewTestCase):
    def test_main_page_is_ok(self):
        self.assert200(self.client.get('/'))

    def test_about_page_is_ok(self):
        self.assert200(self.client.get('/about'))

    def test_nonexistent_page_is_not_found(self):
        self.assert404(self.client.get('/nonexistent'))
