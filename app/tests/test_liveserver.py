from app.factory import create_app

from flask.ext.testing import LiveServerTestCase

from .test_views import ViewTestCase

from functools import partial
from selenium import webdriver
import unittest

class LiveServerTests(LiveServerTestCase):
    BASE_APP_CONFIG = ViewTestCase.BASE_APP_CONFIG.copy()
    BASE_APP_CONFIG.update(
        WTF_CSRF_ENABLED=True,
        LIVESERVER_PORT=5001
    )

    def create_app(self):
        app = create_app(config=self.BASE_APP_CONFIG)
        app.run = partial(app.run, host='0.0.0.0')
        return app

    @unittest.skip("need to set up an ambassador container")
    def test_foo(self):
        browser = webdriver.Remote(
            command_executor='http://phantomjs:8910/wd/hub',
            desired_capabilities={
              'browserName': 'phantomjs'
            }
        )
        browser.get('http://app:5001')
