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
        self.user = User(email=u'a@example.org', password='foo', active=True)
        db.session.add(self.user)
        db.session.commit()

    def test_it_works(self):
        con = UserConference(conference=u'mycon', user_id=self.user.id)
        db.session.add(con)
        db.session.commit()
        self.assertEqual(len(self.user.conferences), 1)
        user_con = self.user.conferences[0]
        self.assertEqual(user_con.conference.name, 'My Conference')

class ConferencesTests(TestCase):
    def test_from_id_raises_error(self):
        c = Conferences([])
        with self.assertRaises(ValueError):
            c.from_id('foo')

    def test_from_id(self):
        foo = conference_from_yaml(id='foo')
        c = Conferences([foo])
        self.assertEqual(c.from_id('foo'), foo)

    def test_featured(self):
        bar = conference_from_yaml(is_featured=False)
        foo = conference_from_yaml(is_featured=True)

        c = Conferences([bar, foo])
        self.assertEqual(c.featured, [foo])

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
