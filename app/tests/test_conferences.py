import os
import datetime
from unittest import TestCase

from ..conferences import Conference, FILESYSTEM_LOGO_PATH

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
