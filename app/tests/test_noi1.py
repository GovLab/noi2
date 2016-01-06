import datetime
from flask_script import Manager

from .test_models import DbTestCase
from .test_views import ViewTestCase
from .factories import UserFactory

from app import noi1
from app.models import db, Noi1MigrationInfo

SAMPLE_USER = {
    "city": "", 
    "first_name": "Foo", 
    "last_name": "Bar", 
    "domain_expertise": None, 
    "picture": "https://pbs.twimg.com/profile_images/123123_normal.jpeg", 
    "title": "Project Manager", 
    "skills": {
        "opendata/implementing-an-open-data-program/making-machine-readable": "1", 
        "opendata/implementing-an-open-data-program/open-data-standards": "1", 
        "opendata/implementing-an-open-data-program/open-data-formats": "-1",
    },
    "country": "United States", 
    "latlng": "(41.123, -72.123)", 
    "userid": "twitter:123123123", 
    "org_type": "org", 
    "country_code": "US", 
    "timestamp": "2015-06-03T19:47:30.057746", 
    "domains": [], 
    "org": "FooOrg", 
    "langs": [
        "English"
    ], 
    "email": u"foo@example.org", 
    "projects": None
}

class Noi1MigrationInfoTests(DbTestCase):
    def test_is_none_by_default(self):
        user = UserFactory.create(email=u'foo@example.org', password='foo')
        db.session.commit()
        self.assertEqual(user.noi1_migration_info, None)

    def test_is_added_on_import(self):
        user = noi1.add_user_to_db(SAMPLE_USER, password='foo')
        db.session.commit()
        self.assertEqual(user.noi1_migration_info.noi1_userid,
                         'twitter:123123123')
        self.assertEqual(user.noi1_migration_info.email_sent_at, None)

    def test_is_deleted_along_with_user(self):
        user = noi1.add_user_to_db(SAMPLE_USER, password='foo')
        db.session.commit()
        db.session.delete(user)
        db.session.commit()

        query = Noi1MigrationInfo.query.filter(
            Noi1MigrationInfo.noi1_userid == 'twitter:123123123'
        )
        self.assertEqual(len(query.all()), 0)

class EmailSendingTests(ViewTestCase):
    BASE_APP_CONFIG = ViewTestCase.BASE_APP_CONFIG.copy()

    BASE_APP_CONFIG.update(
        MAIL_USERNAME='foo@noi.org',
        NOI_DEPLOY='noi.org',
        SECURITY_EMAIL_SENDER='noreply@noi.org',
        MAIL_SUPPRESS_SEND=True,
    )

    def setUp(self):
        super(EmailSendingTests, self).setUp()
        self.manager = Manager(self.app)
        self.manager.add_command('noi1', noi1.Noi1Command)
        self.mail = self.app.extensions.get('mail')

        noi1.set_users_from_json([SAMPLE_USER])
        self.user = noi1.add_user_to_db(SAMPLE_USER, password='foo')
        db.session.commit()

        assert self.user.noi1_migration_info.email_sent_at is None

    def run_command(self, *args):
        self.manager.handle('', ['noi1'] + list(args))

    def test_send_all_migration_instructions_works(self):
        with self.mail.record_messages() as outbox:
            self.run_command('send_all_migration_instructions')
            self.assertEqual(len(outbox), 1)

        with self.mail.record_messages() as outbox:
            self.run_command('send_all_migration_instructions')
            self.assertEqual(len(outbox), 0)

    def test_send_migration_instructions_works(self):
        with self.mail.record_messages() as outbox:
            self.run_command('send_migration_instructions',
                             'foo@example.org')
            self.assertEqual(len(outbox), 1)
            msg = outbox[0]
            self.assertEqual(msg.sender, 'noreply@noi.org')
            self.assertEqual(msg.recipients, ['foo@example.org'])
            assert 'https://noi.org' in msg.body

            delta = (datetime.datetime.now() -
                     self.user.noi1_migration_info.email_sent_at)

            assert delta.total_seconds() < 60
