from jinja2 import Undefined

from app import utils

from .test_views import ViewTestCase

class NopicAvatarTests(ViewTestCase):
    def assertIsImage(self, url):
        res = self.client.get(url)
        self.assert200(res)
        self.assertRegexpMatches(res.headers['content-type'], r'^image/')

    def test_returns_image_with_undefined(self):
        self.assertIsImage(utils.get_nopic_avatar(Undefined()))

    def test_returns_different_images_with_different_emails(self):
        url1 = utils.get_nopic_avatar('foo@example.org')
        url2 = utils.get_nopic_avatar('bar@example.org')
        url3 = utils.get_nopic_avatar('baz@example.org')

        self.assertNotEqual(url1, url2)
        self.assertNotEqual(url1, url3)
        self.assertNotEqual(url2, url3)

        for url in [url1, url2, url3]:
            self.assertIsImage(url)
