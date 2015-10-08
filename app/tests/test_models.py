from flask import Flask
from flask.ext.testing import TestCase
from nose.tools import eq_
from sqlalchemy.exc import OperationalError, IntegrityError
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2

from .fixtures import load_fixture
from .. import models, LEVELS

db = models.db

PG_USER = 'postgres'
PG_HOST = 'db'
PG_DBNAME = 'noi_test'

# We can't use postgres on Travis CI builds until
# https://github.com/GovLab/noi2/issues/23 is fixed.
USE_POSTGRES = False

if USE_POSTGRES:
    TEST_DB_URL = 'postgres://%s:@%s:5432/%s' % (PG_USER, PG_HOST, PG_DBNAME)
else:
    TEST_DB_URL = 'sqlite://'

def create_postgres_database():
    con = psycopg2.connect(user=PG_USER, host=PG_HOST, dbname='postgres')
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    cur.execute('CREATE DATABASE ' + PG_DBNAME)
    cur.close()
    con.close()

class DbTestCase(TestCase):
    BASE_APP_CONFIG = dict(
        SQLALCHEMY_DATABASE_URI=TEST_DB_URL,
        NOI_DEPLOY='_default',
        SEARCH_DEPLOYMENTS=['_default'],
        SECURITY_PASSWORD_HASH='plaintext'
    )

    def create_app(self):
        app = Flask('test')
        app.config.update(self.BASE_APP_CONFIG)
        db.init_app(app)
        return app

    def setUp(self):
        try:
            db.create_all()
        except OperationalError, e:
            db_noexist_msg = 'database "%s" does not exist' % PG_DBNAME
            if USE_POSTGRES and db_noexist_msg in str(e):
                create_postgres_database()
                db.create_all()
            else:
                raise e

    def tearDown(self):
        db.session.remove()
        db.drop_all()

class UserDbTests(DbTestCase):
    def test_ensure_deployment_has_a_default_setting(self):
        u = models.User(email=u'a@example.org', password='a', active=True)
        db.session.add(u)
        db.session.commit()
        eq_(u.deployment, '_default')

    def test_ensure_user_is_constrained_by_deployment_and_email(self):
        a1 = models.User(email=u'a@example.org', password='a', active=True,
                         deployment='1')
        a2 = models.User(email=u'a@example.org', password='a', active=True,
                         deployment='2')
        db.session.add(a1)
        db.session.add(a2)
        db.session.commit()

        with self.assertRaises(IntegrityError):
            a1 = models.User(email=u'a@example.org', password='u',
                             active=True, deployment='1')
            db.session.add(a1)
            db.session.commit()


class UserMatchDbTests(DbTestCase):
    def setUp(self):
        super(UserMatchDbTests, self).setUp()
        load_fixture()
        self.sly = models.User.query_in_deployment()\
          .filter(models.User.email=='sly@stone.com')\
          .one()

    def test_user_match_i_can_explain(self):
        '''
        This method should provide a list of users who can explain the
        questions this user wants to learn, in descending order of similarity,
        with each of the questions grouped by topic.

        I_CAN_EXPLAIN is scored at '2'
        '''
        self.sly.set_skill('prizes-scoping-the-problem-problem-definition', -1)
        stone_more = models.User.query_in_deployment().filter_by(email='sly@stone-more.com').one()
        stone_more.set_skill('prizes-scoping-the-problem-problem-definition', 2)
        stone_less = models.User.query_in_deployment().filter_by(email='sly@stone-less-knowledgeable.com').one()
        stone_less.set_skill('prizes-scoping-the-problem-problem-definition', 2)
        db.session.add(stone_less)
        db.session.add(stone_more)
        db.session.commit()

        self.assertEquals([(m.user.email, m.questionnaires) for m in self.sly.match(
            LEVELS['LEVEL_I_CAN_EXPLAIN']['score'])],
            [
                ('sly@stone-more.com', [
                    ('Open Data', set([
                        "opendata-open-data-policy-core-mission",
                        "opendata-open-data-policy-sensitive-vs-non-sensitive",
                        "opendata-open-data-policy-crafting-an-open-data-policy",
                        "opendata-open-data-policy-getting-public-input",
                        "opendata-open-data-policy-getting-org-approval"
                    ])),
                    ('Prizes', set([
                        'prizes-scoping-the-problem-problem-definition'
                    ]))
                ]),
                ('sly@stone-less-knowledgeable.com', [
                    ('Prizes', set([
                        'prizes-scoping-the-problem-problem-definition'
                    ]))
                ])
            ])

    def test_user_match_i_can_do_it(self):
        '''
        This method should provide a list of users who can do the
        questions this user wants to learn, in descending order of similarity,
        with each of the questions grouped by topic.

        I_CAN_DO_IT is scored at '5'
        '''
        self.sly.set_skill('prizes-scoping-the-problem-problem-definition', -1)
        paul = models.User.query_in_deployment().filter_by(email='paul@lennon.com').one()
        paul.set_skill('prizes-scoping-the-problem-problem-definition', 5)
        stone_less = models.User.query_in_deployment().filter_by(email='sly@stone-less-knowledgeable.com').one()
        stone_less.set_skill('prizes-scoping-the-problem-problem-definition', 5)
        db.session.add(stone_less)
        db.session.add(paul)
        db.session.commit()

        self.assertEquals([(m.user.email, m.questionnaires) for m in self.sly.match(
            LEVELS['LEVEL_I_CAN_DO_IT']['score'])],
            [('paul@lennon.com',
              [
                  ('Open Data', set([
                      "opendata-open-data-policy-core-mission",
                      "opendata-open-data-policy-sensitive-vs-non-sensitive",
                      "opendata-open-data-policy-crafting-an-open-data-policy",
                      "opendata-open-data-policy-getting-public-input",
                      "opendata-open-data-policy-getting-org-approval",
                      "opendata-implementing-an-open-data-program-scraping-open-data",
                      "opendata-implementing-an-open-data-program-making-machine-readable",
                      "opendata-implementing-an-open-data-program-open-data-formats",
                      "opendata-implementing-an-open-data-program-open-data-license",
                      "opendata-implementing-an-open-data-program-open-data-standards",
                      "opendata-implementing-an-open-data-program-managing-open-data",
                      "opendata-implementing-an-open-data-program-frequency-of-release",
                      "opendata-implementing-an-open-data-program-data-quality-and-integrity"
                  ])),
                  ('Prizes', set([
                      "prizes-scoping-the-problem-problem-definition"
                  ]))
              ]),
             ('sly@stone-less-knowledgeable.com',
              [
                  ('Prizes', set([
                      "prizes-scoping-the-problem-problem-definition"
                  ]))
              ])
            ])

    def test_user_match_i_can_refer(self):
        '''
        This method should provide a list of users who can do provide
        a referral for questions this user wants to learn, in descending order
        of similarity, with each of the questions grouped by topic.

        I_CAN_REFER is scored at '1'
        '''
        self.sly.set_skill('prizes-scoping-the-problem-problem-definition', -1)
        dubya = models.User.query_in_deployment().filter_by(email='dubya@shrub.com').one()
        dubya.set_skill('prizes-scoping-the-problem-problem-definition', 1)
        stone_less = models.User.query_in_deployment().filter_by(email='sly@stone-less-knowledgeable.com').one()
        stone_less.set_skill('prizes-scoping-the-problem-problem-definition', 1)
        db.session.add(stone_less)
        db.session.add(dubya)
        db.session.commit()

        self.assertEquals([(m.user.email, m.questionnaires) for m in self.sly.match(
            LEVELS['LEVEL_I_CAN_REFER']['score'])],
            [('dubya@shrub.com',
              [
                  ('Open Data', set([
                      "opendata-open-data-policy-core-mission",
                      "opendata-open-data-policy-sensitive-vs-non-sensitive",
                      "opendata-open-data-policy-crafting-an-open-data-policy",
                      "opendata-open-data-policy-getting-public-input",
                      "opendata-open-data-policy-getting-org-approval",
                      "opendata-implementing-an-open-data-program-scraping-open-data",
                      "opendata-implementing-an-open-data-program-making-machine-readable",
                      "opendata-implementing-an-open-data-program-open-data-formats",
                      "opendata-implementing-an-open-data-program-open-data-license",
                      "opendata-implementing-an-open-data-program-open-data-standards",
                      "opendata-implementing-an-open-data-program-managing-open-data",
                      "opendata-implementing-an-open-data-program-frequency-of-release",
                      "opendata-implementing-an-open-data-program-data-quality-and-integrity"
                  ])),
                  ('Prizes', set([
                      "prizes-scoping-the-problem-problem-definition"
                  ]))
              ]),
             ('sly@stone-less-knowledgeable.com',
              [
                  ('Prizes', set([
                      "prizes-scoping-the-problem-problem-definition"
                  ]))
              ])
            ])

    def test_user_match_i_want_to_learn(self):
        '''
        This method should provide a list of users who want to learn the same
        things, in descending order of similarity, with each of the questions
        grouped by topic.

        I_WANT_TO_LEARN is scored at -1
        '''
        self.sly.set_skill('prizes-scoping-the-problem-problem-definition', -1)
        stone_more = models.User.query_in_deployment().filter_by(email='sly@stone-more.com').one()
        stone_more.set_skill('prizes-scoping-the-problem-problem-definition', -1)
        stone_less = models.User.query_in_deployment().filter_by(email='sly@stone-less-knowledgeable.com').one()
        stone_less.set_skill('prizes-scoping-the-problem-problem-definition', -1)
        db.session.add(stone_less)
        db.session.add(stone_more)
        db.session.commit()

        self.assertEquals([(m.user.email, m.questionnaires) for m in self.sly.match(
            LEVELS['LEVEL_I_WANT_TO_LEARN']['score'])],
            [('sly@stone-more.com',
              [
                  ('Open Data', set([
                      "opendata-implementing-an-open-data-program-scraping-open-data",
                      "opendata-implementing-an-open-data-program-making-machine-readable",
                      "opendata-implementing-an-open-data-program-open-data-formats",
                      "opendata-implementing-an-open-data-program-open-data-license",
                      "opendata-implementing-an-open-data-program-open-data-standards",
                      "opendata-implementing-an-open-data-program-managing-open-data",
                      "opendata-implementing-an-open-data-program-frequency-of-release",
                      "opendata-implementing-an-open-data-program-data-quality-and-integrity"
                  ])),
                  ('Prizes', set([
                      "prizes-scoping-the-problem-problem-definition"
                  ]))
              ]),
             ('sly@stone-less-knowledgeable.com',
              [
                  ('Open Data', set([
                      "opendata-implementing-an-open-data-program-open-data-standards",
                      "opendata-implementing-an-open-data-program-managing-open-data",
                      "opendata-implementing-an-open-data-program-frequency-of-release",
                      "opendata-implementing-an-open-data-program-data-quality-and-integrity"
                  ])),
                  ('Prizes', set([
                      "prizes-scoping-the-problem-problem-definition"
                  ]))
              ])
            ])


class UserSkillDbTests(DbTestCase):
    def setUp(self):
        super(UserSkillDbTests, self).setUp()
        load_fixture()
        self.sly_less = models.User.query_in_deployment()\
          .filter(models.User.email=='sly@stone-less-knowledgeable.com')\
          .one()

    def test_get_most_complete_profiles_works(self):
        user_scores = models.User.get_most_complete_profiles()
        self.assertEqual(user_scores.all()[-1][0].email, 'sly@stone-less-knowledgeable.com')
        # should exclude invisible deployments
        self.assertEqual(user_scores.count(), 5)

        # should respect limit
        user_scores = models.User.get_most_complete_profiles(limit=3)
        self.assertEqual(user_scores.count(), 3)

    def test_questionnaire_progress_works(self):
        progress = self.sly_less.questionnaire_progress
        self.assertEqual(progress['opendata']['answered'], 4)
        self.assertEqual(progress['prizes']['answered'], 0)

    def test_skill_levels_works(self):
        self.assertEqual(self.sly_less.skill_levels, {
            u'opendata-implementing-an-open-data-program-data-quality-and-integrity': -1,
            u'opendata-implementing-an-open-data-program-frequency-of-release': -1,
            u'opendata-implementing-an-open-data-program-managing-open-data': -1,
            u'opendata-implementing-an-open-data-program-open-data-standards': -1
        })

    def test_helpful_users_works(self):
        '''
        Make sure that helpful users ranks users based off of most helpful
        answers, and sticks to the proper deployment.
        '''
        sly_more = models.User.query.filter_by(email='sly@stone-more.com').one()
        outsider = models.User(email=u'a@example.org', password='a', active=True,
                               deployment='2')
        db.session.add(outsider)
        db.session.commit()

        self.assertEqual([(user.email, score) for user, score in sly_more.helpful_users],
                         [(u'paul@lennon.com', 48L),
                          (u'dubya@shrub.com', 16L),
                          (u'sly@stone-less-knowledgeable.com', 0L),
                          (u'sly@stone.com', 0L)])

    def test_nearest_neighbors_works(self):
        '''
        Make sure that nearest neighbors ranks proximity of users correctly,
        and only within the existing deployment.
        '''
        sly_more = models.User.query.filter_by(email='sly@stone-more.com').one()
        outsider = models.User(email=u'a@example.org', password='a', active=True,
                               deployment='2')
        db.session.add(outsider)
        db.session.commit()

        self.assertEqual([(user.email, score) for user, score in sly_more.nearest_neighbors],
                         [(u'sly@stone.com', 15),
                          (u'dubya@shrub.com', 21),
                          (u'paul@lennon.com', 63),
                          (u'sly@stone-less-knowledgeable.com', 108)])

class UserRegistrationDbTests(DbTestCase):
    def setUp(self):
        super(UserRegistrationDbTests, self).setUp()
        user = models.User(email=u'a@example.org', password='a', active=True)
        db.session.add(user)
        db.session.commit()
        self.user = user

    def test_user_is_not_fully_registered_by_default(self):
        eq_(self.user.has_fully_registered, False)

    def test_set_fully_registered_works(self):
        self.user.set_fully_registered()
        eq_(self.user.has_fully_registered, True)

    def test_multiple_join_events_are_not_created(self):
        self.user.set_fully_registered()
        self.user.set_fully_registered()
        join_events = db.session.query(models.UserJoinedEvent).\
                      filter_by(user_id=self.user.id).\
                      all()
        eq_(len(join_events), 1)

class SharedMessageDbTests(DbTestCase):
    def test_only_events_in_deployments_are_seen(self):
        other = models.User(email=u'b@example.org', password='a', active=True,
                            deployment='other')
        a = models.User(email=u'a@example.org', password='a', active=True,
                        deployment='_default')
        db.session.add(other)
        db.session.add(a)
        db.session.commit()
        message1 = models.SharedMessageEvent.from_user(a, message="hi")
        message2 = models.SharedMessageEvent.from_user(other, message="other")
        db.session.add(message1)
        db.session.add(message2)
        db.session.commit()
        messages = models.Event.query_in_deployment()
        eq_(messages.count(), 1)
        eq_(messages[0].type, 'shared_message')
        eq_(messages[0].message, 'hi')
        eq_(messages[0].user.email, 'a@example.org')

def test_users_only_display_in_search_if_they_have_first_and_last_name():
    user = models.User()
    eq_(user.display_in_search, False)
    user.first_name = "John"
    eq_(user.display_in_search, False)
    user.last_name = "Doe"
    eq_(user.display_in_search, True)


class ConnectionEventDbTests(DbTestCase):
    '''
    Tests for adding connections
    '''
    def setUp(self):
        super(ConnectionEventDbTests, self).setUp()
        load_fixture()
        self.sly_less = models.User.query_in_deployment()\
          .filter(models.User.email == 'sly@stone-less-knowledgeable.com')\
          .one()

    def test_creates_connection_event(self):
        '''
        Adding connections should create one event.
        '''
        dubya = models.User.query_in_deployment().filter_by(email='dubya@shrub.com').one()
        lennon = models.User.query_in_deployment().filter_by(email='paul@lennon.com').one()
        stone = models.User.query_in_deployment().filter_by(email='sly@stone.com').one()
        event = self.sly_less.email_connect([dubya, lennon])
        event.set_total_connections()
        db.session.commit()
        connection_events = models.ConnectionEvent.query.all()
        self.assertEquals(len(connection_events), 1)
        connection_event = connection_events[-1]
        self.assertEquals(connection_event.emails.count(), 2)
        self.assertEquals(models.ConnectionEvent.connections_in_deployment(), 2)
        self.assertEquals(connection_event.total_connections, 2)

        # second connect shouldn't do anything, since no new connections made
        event = self.sly_less.email_connect([dubya, lennon])
        event.set_total_connections()
        db.session.commit()
        connection_events = models.ConnectionEvent.query.all()
        self.assertEquals(len(connection_events), 2)
        connection_event = connection_events[-1]
        self.assertEquals(connection_event.emails.count(), 2)
        self.assertEquals(models.ConnectionEvent.connections_in_deployment(), 2)
        self.assertEquals(connection_event.total_connections, 2)

        # this should add one more
        event = self.sly_less.email_connect([lennon, stone])
        event.set_total_connections()
        db.session.commit()
        connection_events = models.ConnectionEvent.query.all()
        self.assertEquals(len(connection_events), 3)
        connection_event = connection_events[-1]
        self.assertEquals(connection_event.emails.count(), 2)
        self.assertEquals(models.ConnectionEvent.connections_in_deployment(), 3)
        self.assertEquals(connection_event.total_connections, 3)

class UserConnectionDbTests(DbTestCase):
    '''
    Tests for connections between users.
    '''

    def setUp(self):
        super(UserConnectionDbTests, self).setUp()
        load_fixture()
        self.sly_less = models.User.query_in_deployment()\
          .filter(models.User.email == 'sly@stone-less-knowledgeable.com')\
          .one()

    def test_user_no_connections(self):
        '''
        A user initially has no connections.
        '''
        self.assertEquals(self.sly_less.connections, 0)

    def test_user_no_self_connections(self):
        '''
        A user cannot connect with themselves.
        '''
        self.sly_less.email_connect([self.sly_less])
        db.session.commit()
        self.assertEquals(self.sly_less.connections, 0)

    def test_user_connect_on_email_one(self):
        '''
        A user gains a connection on emailing someone.
        '''
        self.sly_less.email_connect([
            models.User.query_in_deployment().filter_by(email='paul@lennon.com').one()
        ])
        db.session.commit()
        self.assertEquals(self.sly_less.connections, 1)

    def test_user_connect_on_email_several(self):
        '''
        A user gains several connections on emailing several people.
        '''
        dubya = models.User.query_in_deployment().filter_by(email='dubya@shrub.com').one()
        lennon = models.User.query_in_deployment().filter_by(email='paul@lennon.com').one()
        stone = models.User.query_in_deployment().filter_by(email='sly@stone.com').one()
        self.sly_less.email_connect([dubya, lennon, stone])
        db.session.commit()
        self.assertEquals(self.sly_less.connections, 3)

    def test_user_connect_reciprocal(self):
        '''
        A user's connections are reciprocal.
        '''
        dubya = models.User.query_in_deployment().filter_by(email='dubya@shrub.com').one()
        lennon = models.User.query_in_deployment().filter_by(email='paul@lennon.com').one()
        stone = models.User.query_in_deployment().filter_by(email='sly@stone.com').one()
        self.sly_less.email_connect([dubya, lennon, stone])
        db.session.commit()
        self.assertEquals(dubya.connections, 1)
        self.assertEquals(lennon.connections, 1)
        self.assertEquals(stone.connections, 1)

    def test_user_connect_on_email_noduplicate(self):
        '''
        Emailing one person several times does not result in additional
        connections.
        '''
        paul = models.User.query_in_deployment().filter_by(email='paul@lennon.com').one()
        for _ in xrange(0, 3):
            self.sly_less.email_connect([paul])
        db.session.commit()
        self.assertEquals(self.sly_less.connections, 1)

    def test_user_get_most_complete_profiles_works(self):
        '''
        Make sure the `get_most_complete_profiles` endpoint works.
        '''
        dubya = models.User.query_in_deployment().filter_by(email='dubya@shrub.com').one()
        lennon = models.User.query_in_deployment().filter_by(email='paul@lennon.com').one()
        stone = models.User.query_in_deployment().filter_by(email='sly@stone.com').one()
        self.assertEquals(models.Email.query.count(), 0)
        self.assertEquals([(u.email, score) for u, score in models.User.get_most_connected_profiles()],
                          [])
        self.sly_less.email_connect([dubya, lennon, stone])
        lennon.email_connect([dubya])
        db.session.commit()
        self.assertEquals(models.Email.query.count(), 4)
        self.assertEquals([(u.email, score) for u, score in models.User.get_most_connected_profiles()],
                          [(self.sly_less.email, 3),
                           (dubya.email, 2),
                           (lennon.email, 2),
                           (stone.email, 1)])
