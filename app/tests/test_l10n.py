import os
from babel.messages.pofile import read_po
from babel.messages.catalog import TranslationError, Message
from babel.messages import checkers

from .test_views import ViewTestCase
from .util import eq_, create_empty_flask_app
from app import l10n

def test_flask_security_strings_do_not_interpolate():
    app = create_empty_flask_app()
    l10n.configure_app(app)
    eq_(unicode(app.config['SECURITY_MSG_EMAIL_ALREADY_ASSOCIATED'][0]),
        '%(email)s is already associated with an account.')

def test_all_translations_exist():
    dirs = os.listdir('/noi/app/translations')
    for locale in l10n.TRANSLATIONS:
        if str(locale) not in dirs:
            raise Exception('Locale %s does not exist' % locale)

class LocalizationTests(ViewTestCase):
    def test_locale_is_en_by_default(self):
        res = self.client.get('/')
        assert '<html lang="en"' in res.data

    def test_locale_in_session_is_respected(self):
        assert 'es' in l10n.VALID_LOCALE_CODES
        with self.client.session_transaction() as sess:
            l10n.change_session_locale('es', session=sess)
        res = self.client.get('/')
        assert '<html lang="es"' in res.data

    def test_locale_in_accept_language_header_is_respected(self):
        assert 'es' in l10n.VALID_LOCALE_CODES
        res = self.client.get('/', headers={
            'Accept-Language': 'es'
        })
        assert '<html lang="es"' in res.data

def check_sources_without_named_placeholders_work(catalog, msg):
    if '%(' in msg.string and '%(' not in msg.id:
        raise TranslationError("Translation contains named placeholder "
                               "but source doesn't: %s" % msg.string)

checkers.checkers.append(check_sources_without_named_placeholders_work)

def test_checker_works():
    m = Message(id=u'hello', string=u'hello %(num)d')
    errors = [err for err in m.check()]
    eq_(len(errors), 1)
    eq_(str(errors[0]), 'Translation contains named placeholder but '
                        'source doesn\'t: hello %(num)d')

def _make_pofile_test(locale):
    def test_pofile():
        pofile = open(
            '/noi/app/translations/%s/LC_MESSAGES/messages.po' % locale,
            'r'
        )
        catalog = read_po(pofile)
        errors = catalog.check()
        eq_([error for error in errors], [])

    test_pofile.__name__ = 'test_pofile_%s' % locale
    globals()[test_pofile.__name__] = test_pofile

for locale in l10n.TRANSLATIONS:
    _make_pofile_test(locale)
