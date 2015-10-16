import os
from flask import Flask
from nose.tools import eq_

from .test_views import ViewTestCase
from app import l10n

def test_flask_security_strings_do_not_interpolate():
    app = Flask('test')
    l10n.configure_app(app)
    eq_(unicode(app.config['SECURITY_MSG_EMAIL_ALREADY_ASSOCIATED'][0]),
        '%(email)s is already associated with an account.')

class LocalizationTests(ViewTestCase):
    def test_all_translations_exist(self):
        dirs = os.listdir('/noi/app/translations')
        for locale in l10n.TRANSLATIONS:
            if locale not in dirs:
                self.fail('Locale %s does not exist' % locale)

    def test_locale_is_en_by_default(self):
        res = self.client.get('/')
        assert '<html lang="en"' in res.data

    def test_locale_in_accept_language_header_is_respected(self):
        assert 'es_MX' in l10n.TRANSLATIONS
        res = self.client.get('/', headers={
            'Accept-Language': 'es_MX'
        })
        assert '<html lang="es"' in res.data
