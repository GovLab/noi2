import os
import datetime
from unittest import TestCase

from ..conferences import Conferences, Conference, FILESYSTEM_LOGO_PATH
from ..models import db, User, UserConference
from .test_models import DbTestCase

if not os.path.exists(FILESYSTEM_LOGO_PATH):
    os.mkdir(FILESYSTEM_LOGO_PATH)

def conference_from_yaml(**kwargs):
    c = {
        'id': 'bar',
        'name': 'The Bar Conference',
        'url': 'http://example.org',
        'start_date': '2016-01-01'
    }
    c.update(kwargs)
    return Conference.from_yaml(c)

class UserConferenceTests(DbTestCase):
    BASE_APP_CONFIG = DbTestCase.BASE_APP_CONFIG.copy()
    BASE_APP_CONFIG['CONFERENCES'] = Conferences([
        conference_from_yaml(id=u'mycon', name=u'My Conference')
    ])

    def setUp(self):
        super(UserConferenceTests, self).setUp()
        self.mycon = self.app.config['CONFERENCES'].from_id('mycon')
        self.user = User(email=u'a@example.org', password='foo', active=True)
        db.session.add(self.user)
        db.session.commit()

    def test_setting_user_conference_ids_adds_conferences(self):
        self.user.conference_ids = ['mycon']
        db.session.commit()
        self.assertEqual(self.user.conference_objects, [self.mycon])

    def test_setting_user_conference_ids_removes_conferences(self):
        self.user.conference_ids = ['mycon']
        db.session.commit()
        self.user.conference_ids = []
        db.session.commit()
        self.assertEqual(self.user.conference_objects, [])

    def test_adding_user_conferences_works(self):
        con = UserConference(conference=u'mycon', user_id=self.user.id)
        db.session.add(con)
        db.session.commit()
        self.assertEqual(self.user.conference_objects, [self.mycon])

class ConferencesTests(TestCase):
    def test_from_id_raises_error(self):
        c = Conferences([])
        with self.assertRaises(ValueError):
            c.from_id('foo')

    def test_from_id(self):
        foo = conference_from_yaml(id='foo')
        c = Conferences([foo])
        self.assertEqual(c.from_id('foo'), foo)

    def test_choices(self):
        c = Conferences([conference_from_yaml(id='foo', name='Foo'),
                         conference_from_yaml(id='bar', name='Bar')])
        self.assertEqual(c.choices(), [('foo', 'Foo'), ('bar', 'Bar')])
        self.assertTrue(isinstance(c.choices(), Conferences))

    def test_featured(self):
        bar = conference_from_yaml(is_featured=False)
        foo = conference_from_yaml(is_featured=True)

        c = Conferences([bar, foo])
        self.assertEqual(c.featured, [foo])
        self.assertTrue(isinstance(c.featured, Conferences))

class ConferenceTests(TestCase):
    def test_parses_start_date(self):
        c = conference_from_yaml(start_date='2016-02-01')
        self.assertEqual(c.start_date, datetime.date(2016, 02, 01))

    def test_invalid_logo_filename_raises_error(self):
        with self.assertRaisesRegexp(ValueError, 'Logo does not exist'):
            c = conference_from_yaml(logo_filename='_TEST_nonexistent.png')

    def test_valid_logo_filename_raises_no_error(self):
        filename = '_TEST_logo.png'
        abs_filename = FILESYSTEM_LOGO_PATH + '/' + filename
        f = open(abs_filename, 'w')
        f.close()

        try:
            c = conference_from_yaml(logo_filename=filename)
        finally:
            os.unlink(abs_filename)
