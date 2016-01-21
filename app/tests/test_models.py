import time
import StringIO
import contextlib
from flask import Flask
from flask_testing import TestCase
from nose.tools import eq_
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy_utils import Country
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2

from .factories import UserFactory, UserSkillFactory
from .. import models, LEVELS, babel

db = models.db

PG_USER = 'postgres'
PG_HOST = 'db'
PG_DBNAME = 'noi_test'

USE_POSTGRES = True

if USE_POSTGRES:
    TEST_DB_URL = 'postgres://%s:@%s:5432/%s' % (PG_USER, PG_HOST, PG_DBNAME)
else:
    TEST_DB_URL = 'sqlite://'

def wait_until_db_is_ready(max_tries=20):
    if not USE_POSTGRES: return

    attempts = 0
    connected = False

    while not connected:
        try:
            psycopg2.connect(user=PG_USER, host=PG_HOST, dbname='postgres')
            connected = True
        except psycopg2.OperationalError, e:
            if ('could not connect to server' not in str(e) and
                'the database system is starting up' not in str(e)):
                raise
            attempts += 1
            if attempts >= max_tries:
                raise
            time.sleep(0.5)

def get_postgres_create_table_sql():
    output = StringIO.StringIO()

    def dump(sql, *multiparams, **params):
        output.write(sql.compile(dialect=engine.dialect))

    engine = create_engine('postgresql://', strategy='mock', executor=dump)
    db.metadata.create_all(engine, checkfirst=False)

    return output.getvalue()

def create_postgres_database():
    con = psycopg2.connect(user=PG_USER, host=PG_HOST, dbname='postgres')
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    cur.execute('CREATE DATABASE ' + PG_DBNAME)
    cur.close()
    con.close()

def db_test_request_context():
    app = Flask('minimal_db_app')
    app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DB_URL
    db.init_app(app)
    return app.test_request_context()

def create_tables():
    try:
        db.create_all()
    except OperationalError, e:
        db_noexist_msg = 'database "%s" does not exist' % PG_DBNAME
        if USE_POSTGRES and db_noexist_msg in str(e):
            create_postgres_database()
            db.create_all()
        else:
            raise e

def drop_tables():
    db.drop_all()

def empty_tables():
    # http://stackoverflow.com/a/5003705/2422398
    with contextlib.closing(db.engine.connect()) as conn:
        transaction = conn.begin()
        for table in reversed(db.Model.metadata.sorted_tables):
            conn.execute(table.delete())
        transaction.commit()

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

    def tearDown(self):
        db.session.remove()
        empty_tables()

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


class UserMatchAgainstDbTests(DbTestCase):
    def setUp(self):
        super(UserMatchAgainstDbTests, self).setUp()
        self.jack = UserFactory.create(
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-open-data-policy-core-mission": -1,
                "opendata-open-data-policy-sensitive-vs-non-sensitive": -1,
                "opendata-open-data-policy-crafting-an-open-data-policy": -1,
                "opendata-open-data-policy-getting-public-input": -1,
                "opendata-open-data-policy-getting-org-approval": -1,
                "opendata-implementing-an-open-data-program-scraping-open-data": -1,
                "opendata-implementing-an-open-data-program-making-machine-readable": -1,
                "opendata-implementing-an-open-data-program-open-data-formats": -1,
                "opendata-implementing-an-open-data-program-open-data-license": -1,
                "opendata-implementing-an-open-data-program-open-data-standards": -1,
                "opendata-implementing-an-open-data-program-managing-open-data": -1,
                "opendata-implementing-an-open-data-program-frequency-of-release": -1,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": -1,
                "prizes-scoping-the-problem-problem-definition": -1,
                "prizes-scoping-the-problem-research": -1,
                "prizes-scoping-the-problem-progress-metrics": -1,
                "prizes-designing-for-a-successful-prize-when-to-use-a-prize": -1,
                "prizes-designing-for-a-successful-prize-grand-challenge": -1,
                "prizes-designing-for-a-successful-prize-prizes-incentives": -1,
                "prizes-designing-for-a-successful-prize-prize-amount": -1,
                "prizes-identifying-the-right-audience-audience": -1
            }.items()])
        self.jill = UserFactory.create(
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-open-data-policy-core-mission": -1,
                "opendata-open-data-policy-sensitive-vs-non-sensitive": -1,
                "opendata-open-data-policy-crafting-an-open-data-policy": -1,
                "opendata-open-data-policy-getting-public-input": -1,
                "opendata-open-data-policy-getting-org-approval": -1,
                "opendata-implementing-an-open-data-program-scraping-open-data": 1,
                "opendata-implementing-an-open-data-program-making-machine-readable": 1,
                "opendata-implementing-an-open-data-program-open-data-formats": 1,
                "opendata-implementing-an-open-data-program-open-data-license": 2,
                "opendata-implementing-an-open-data-program-open-data-standards": 2,
                "opendata-implementing-an-open-data-program-managing-open-data": 2,
                "opendata-implementing-an-open-data-program-frequency-of-release": 5,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": 5,
                "prizes-scoping-the-problem-problem-definition": -1,
                "prizes-scoping-the-problem-research": -1,
                "prizes-scoping-the-problem-progress-metrics": 1,
                "prizes-designing-for-a-successful-prize-when-to-use-a-prize": 2,
                "prizes-designing-for-a-successful-prize-grand-challenge": 5,
                "prizes-designing-for-a-successful-prize-prizes-incentives": 5,
                "prizes-designing-for-a-successful-prize-prize-amount": 5,
                "prizes-identifying-the-right-audience-audience": 5
            }.items()])
        db.session.commit()

    def test_user_match_against(self):
        '''

        '''
        learn = LEVELS['LEVEL_I_WANT_TO_LEARN']['score']
        refer = LEVELS['LEVEL_I_CAN_REFER']['score']
        explain = LEVELS['LEVEL_I_CAN_EXPLAIN']['score']
        do_it = LEVELS['LEVEL_I_CAN_DO_IT']['score']
        self.assertEqual(self.jack.match_against(self.jill), [
            ('opendata', 13, {
                learn: set([
                    "opendata-open-data-policy-core-mission",
                    "opendata-open-data-policy-sensitive-vs-non-sensitive",
                    "opendata-open-data-policy-crafting-an-open-data-policy",
                    "opendata-open-data-policy-getting-public-input",
                    "opendata-open-data-policy-getting-org-approval"
                ]),
                refer: set([
                    "opendata-implementing-an-open-data-program-scraping-open-data",
                    "opendata-implementing-an-open-data-program-making-machine-readable",
                    "opendata-implementing-an-open-data-program-open-data-formats",
                ]),
                explain: set([
                    "opendata-implementing-an-open-data-program-open-data-license",
                    "opendata-implementing-an-open-data-program-open-data-standards",
                    "opendata-implementing-an-open-data-program-managing-open-data",
                ]),
                do_it: set([
                    "opendata-implementing-an-open-data-program-frequency-of-release",
                    "opendata-implementing-an-open-data-program-data-quality-and-integrity",
                ])
            }),
            ('prizes', 8, {
                learn: set([
                    "prizes-scoping-the-problem-problem-definition",
                    "prizes-scoping-the-problem-research",
                ]),
                refer: set([
                    "prizes-scoping-the-problem-progress-metrics",
                ]),
                explain: set([
                    "prizes-designing-for-a-successful-prize-when-to-use-a-prize",
                ]),
                do_it: set([
                    "prizes-designing-for-a-successful-prize-grand-challenge",
                    "prizes-designing-for-a-successful-prize-prizes-incentives",
                    "prizes-designing-for-a-successful-prize-prize-amount",
                    "prizes-identifying-the-right-audience-audience",
                ])
            })
        ])

        self.assertEqual(self.jill.match_against(self.jack), [
            ('opendata', 5, {
                learn: set([
                    "opendata-open-data-policy-core-mission",
                    "opendata-open-data-policy-sensitive-vs-non-sensitive",
                    "opendata-open-data-policy-crafting-an-open-data-policy",
                    "opendata-open-data-policy-getting-public-input",
                    "opendata-open-data-policy-getting-org-approval",
                ])
            }),
            ('prizes', 2, {
                learn: set([
                    "prizes-scoping-the-problem-problem-definition",
                    "prizes-scoping-the-problem-research",
                ])
            })
        ])


class UserMatchDbTests(DbTestCase):
    def setUp(self):
        super(UserMatchDbTests, self).setUp()
        self.outsider = UserFactory.create(
            first_name=u"outsider",
            last_name=u"jones",
            email=u"sly@stone.com",
            deployment=u"sword_coast",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-open-data-policy-core-mission": 2,
                "opendata-open-data-policy-sensitive-vs-non-sensitive": 2,
                "opendata-open-data-policy-crafting-an-open-data-policy": 2,
                "opendata-open-data-policy-getting-public-input": 2,
                "opendata-open-data-policy-getting-org-approval": 2,
                "opendata-implementing-an-open-data-program-scraping-open-data": 2,
                "opendata-implementing-an-open-data-program-making-machine-readable": 2,
                "opendata-implementing-an-open-data-program-open-data-formats": -1,
                "opendata-implementing-an-open-data-program-open-data-license": -1,
                "opendata-implementing-an-open-data-program-open-data-standards": -1,
                "opendata-implementing-an-open-data-program-managing-open-data": -1,
                "opendata-implementing-an-open-data-program-frequency-of-release": -1,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": -1
            }.items()])

        self.sly = UserFactory.create(
            first_name=u"sly",
            last_name=u"stone",
            email=u"sly@stone.com",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-open-data-policy-core-mission": -1,
                "opendata-open-data-policy-sensitive-vs-non-sensitive": -1,
                "opendata-open-data-policy-crafting-an-open-data-policy": -1,
                "opendata-open-data-policy-getting-public-input": -1,
                "opendata-open-data-policy-getting-org-approval": -1,
                "opendata-implementing-an-open-data-program-scraping-open-data": -1,
                "opendata-implementing-an-open-data-program-making-machine-readable": -1,
                "opendata-implementing-an-open-data-program-open-data-formats": -1,
                "opendata-implementing-an-open-data-program-open-data-license": -1,
                "opendata-implementing-an-open-data-program-open-data-standards": -1,
                "opendata-implementing-an-open-data-program-managing-open-data": -1,
                "opendata-implementing-an-open-data-program-frequency-of-release": -1,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": -1
            }.items()])

        self.sly_more = UserFactory.create(
            first_name=u"sly",
            last_name=u"stone-more-knowledgeable",
            email=u"sly@stone-more.com",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-open-data-policy-core-mission": 2,
                "opendata-open-data-policy-sensitive-vs-non-sensitive": 2,
                "opendata-open-data-policy-crafting-an-open-data-policy": 2,
                "opendata-open-data-policy-getting-public-input": 2,
                "opendata-open-data-policy-getting-org-approval": 2,
                "opendata-implementing-an-open-data-program-scraping-open-data": -1,
                "opendata-implementing-an-open-data-program-making-machine-readable": -1,
                "opendata-implementing-an-open-data-program-open-data-formats": -1,
                "opendata-implementing-an-open-data-program-open-data-license": -1,
                "opendata-implementing-an-open-data-program-open-data-standards": -1,
                "opendata-implementing-an-open-data-program-managing-open-data": -1,
                "opendata-implementing-an-open-data-program-frequency-of-release": -1,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": -1
            }.items()])

        self.sly_less = UserFactory.create(
            first_name=u"sly",
            last_name=u"stone-less-knowledgeable",
            email=u"sly@stone-less-knowledgeable.com",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-implementing-an-open-data-program-open-data-standards": -1,
                "opendata-implementing-an-open-data-program-managing-open-data": -1,
                "opendata-implementing-an-open-data-program-frequency-of-release": -1,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": -1
            }.items()])

        self.paul_lennon = UserFactory.create(
            first_name=u"paul",
            last_name=u"lennon",
            email=u"paul@lennon.com",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-open-data-policy-core-mission": 5,
                "opendata-open-data-policy-sensitive-vs-non-sensitive": 5,
                "opendata-open-data-policy-crafting-an-open-data-policy": 5,
                "opendata-open-data-policy-getting-public-input": 5,
                "opendata-open-data-policy-getting-org-approval": 5,
                "opendata-implementing-an-open-data-program-scraping-open-data": 5,
                "opendata-implementing-an-open-data-program-making-machine-readable": 5,
                "opendata-implementing-an-open-data-program-open-data-formats": 5,
                "opendata-implementing-an-open-data-program-open-data-license": 5,
                "opendata-implementing-an-open-data-program-open-data-standards": 5,
                "opendata-implementing-an-open-data-program-managing-open-data": 5,
                "opendata-implementing-an-open-data-program-frequency-of-release": 5,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": 5
            }.items()])

        self.dubya_shrub = UserFactory.create(
            first_name=u"dubya",
            last_name=u"shrub",
            email=u"dubya@shrub.com",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-open-data-policy-core-mission": 1,
                "opendata-open-data-policy-sensitive-vs-non-sensitive": 1,
                "opendata-open-data-policy-crafting-an-open-data-policy": 1,
                "opendata-open-data-policy-getting-public-input": 1,
                "opendata-open-data-policy-getting-org-approval": 1,
                "opendata-implementing-an-open-data-program-scraping-open-data": 1,
                "opendata-implementing-an-open-data-program-making-machine-readable": 1,
                "opendata-implementing-an-open-data-program-open-data-formats": 1,
                "opendata-implementing-an-open-data-program-open-data-license": 1,
                "opendata-implementing-an-open-data-program-open-data-standards": 1,
                "opendata-implementing-an-open-data-program-managing-open-data": 1,
                "opendata-implementing-an-open-data-program-frequency-of-release": 1,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": 1
            }.items()])
        db.session.commit()

    def test_user_match_i_can_explain(self):
        '''
        This method should provide a list of users who can explain the
        questions this user wants to learn, in descending order of similarity,
        with each of the questions grouped by topic.

        I_CAN_EXPLAIN is scored at '2'
        '''
        self.sly.set_skill('prizes-scoping-the-problem-problem-definition', -1)
        self.sly_more.set_skill('prizes-scoping-the-problem-problem-definition', 2)
        self.sly_less.set_skill('prizes-scoping-the-problem-problem-definition', 2)
        db.session.add(self.sly_more)
        db.session.add(self.sly_less)
        db.session.commit()

        self.assertEquals([(m.user.email, m.questionnaires) for m in self.sly.match(
            LEVELS['LEVEL_I_CAN_EXPLAIN']['score'])],
            [
                ('sly@stone-more.com', [
                    ('opendata', set([
                        "opendata-open-data-policy-core-mission",
                        "opendata-open-data-policy-sensitive-vs-non-sensitive",
                        "opendata-open-data-policy-crafting-an-open-data-policy",
                        "opendata-open-data-policy-getting-public-input",
                        "opendata-open-data-policy-getting-org-approval"
                    ])),
                    ('prizes', set([
                        'prizes-scoping-the-problem-problem-definition'
                    ]))
                ]),
                ('sly@stone-less-knowledgeable.com', [
                    ('prizes', set([
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
        self.paul_lennon.set_skill('prizes-scoping-the-problem-problem-definition', 5)
        self.sly_less.set_skill('prizes-scoping-the-problem-problem-definition', 5)
        db.session.add(self.paul_lennon)
        db.session.add(self.sly_less)
        db.session.commit()

        self.assertEquals([(m.user.email, m.questionnaires) for m in self.sly.match(
            LEVELS['LEVEL_I_CAN_DO_IT']['score'])],
            [('paul@lennon.com',
              [
                  ('opendata', set([
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
                  ('prizes', set([
                      "prizes-scoping-the-problem-problem-definition"
                  ]))
              ]),
             ('sly@stone-less-knowledgeable.com',
              [
                  ('prizes', set([
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
        self.dubya_shrub.set_skill('prizes-scoping-the-problem-problem-definition', 1)
        self.sly_less.set_skill('prizes-scoping-the-problem-problem-definition', 1)
        db.session.add(self.dubya_shrub)
        db.session.add(self.sly_less)
        db.session.commit()

        self.assertEquals([(m.user.email, m.questionnaires) for m in self.sly.match(
            LEVELS['LEVEL_I_CAN_REFER']['score'])],
            [('dubya@shrub.com',
              [
                  ('opendata', set([
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
                  ('prizes', set([
                      "prizes-scoping-the-problem-problem-definition"
                  ]))
              ]),
             ('sly@stone-less-knowledgeable.com',
              [
                  ('prizes', set([
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
        self.sly_more.set_skill('prizes-scoping-the-problem-problem-definition', -1)
        self.sly_less.set_skill('prizes-scoping-the-problem-problem-definition', -1)
        db.session.add(self.sly_less)
        db.session.add(self.sly_more)
        db.session.commit()

        self.assertEquals([(m.user.email, m.questionnaires) for m in self.sly.match(
            LEVELS['LEVEL_I_WANT_TO_LEARN']['score'])],
            [('sly@stone-more.com',
              [
                  ('opendata', set([
                      "opendata-implementing-an-open-data-program-scraping-open-data",
                      "opendata-implementing-an-open-data-program-making-machine-readable",
                      "opendata-implementing-an-open-data-program-open-data-formats",
                      "opendata-implementing-an-open-data-program-open-data-license",
                      "opendata-implementing-an-open-data-program-open-data-standards",
                      "opendata-implementing-an-open-data-program-managing-open-data",
                      "opendata-implementing-an-open-data-program-frequency-of-release",
                      "opendata-implementing-an-open-data-program-data-quality-and-integrity"
                  ])),
                  ('prizes', set([
                      "prizes-scoping-the-problem-problem-definition"
                  ]))
              ]),
             ('sly@stone-less-knowledgeable.com',
              [
                  ('opendata', set([
                      "opendata-implementing-an-open-data-program-open-data-standards",
                      "opendata-implementing-an-open-data-program-managing-open-data",
                      "opendata-implementing-an-open-data-program-frequency-of-release",
                      "opendata-implementing-an-open-data-program-data-quality-and-integrity"
                  ])),
                  ('prizes', set([
                      "prizes-scoping-the-problem-problem-definition"
                  ]))
              ])
            ])


class UserSkillDbTests(DbTestCase):
    def setUp(self):
        super(UserSkillDbTests, self).setUp()
        self.outsider = UserFactory.create(
            first_name=u"outsider",
            last_name=u"jones",
            email=u"sly@stone.com",
            deployment=u"sword_coast",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in [
                ("opendata-open-data-policy-core-mission", 2),
                ("opendata-open-data-policy-sensitive-vs-non-sensitive", 2),
                ("opendata-open-data-policy-crafting-an-open-data-policy", 2),
                ("opendata-open-data-policy-getting-public-input", 2),
                ("opendata-open-data-policy-getting-org-approval", 2),
                ("opendata-implementing-an-open-data-program-scraping-open-data", 2),
                ("opendata-implementing-an-open-data-program-making-machine-readable", 2),
                ("opendata-implementing-an-open-data-program-open-data-formats", -1),
                ("opendata-implementing-an-open-data-program-open-data-license", -1),
                ("opendata-implementing-an-open-data-program-open-data-standards", -1),
                ("opendata-implementing-an-open-data-program-managing-open-data", -1),
                ("opendata-implementing-an-open-data-program-frequency-of-release", -1),
                ("opendata-implementing-an-open-data-program-data-quality-and-integrity", -1)
            ]])

        self.sly = UserFactory.create(
            first_name=u"sly",
            last_name=u"stone",
            email=u"sly@stone.com",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-open-data-policy-core-mission": -1,
                "opendata-open-data-policy-sensitive-vs-non-sensitive": -1,
                "opendata-open-data-policy-crafting-an-open-data-policy": -1,
                "opendata-open-data-policy-getting-public-input": -1,
                "opendata-open-data-policy-getting-org-approval": -1,
                "opendata-implementing-an-open-data-program-scraping-open-data": -1,
                "opendata-implementing-an-open-data-program-making-machine-readable": -1,
                "opendata-implementing-an-open-data-program-open-data-formats": -1,
                "opendata-implementing-an-open-data-program-open-data-license": -1,
                "opendata-implementing-an-open-data-program-open-data-standards": -1,
                "opendata-implementing-an-open-data-program-managing-open-data": -1,
                "opendata-implementing-an-open-data-program-frequency-of-release": -1,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": -1
            }.items()])

        self.sly_more = UserFactory.create(
            first_name=u"sly",
            last_name=u"stone-more-knowledgeable",
            email=u"sly@stone-more.com",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-open-data-policy-core-mission": 2,
                "opendata-open-data-policy-sensitive-vs-non-sensitive": 2,
                "opendata-open-data-policy-crafting-an-open-data-policy": 2,
                "opendata-open-data-policy-getting-public-input": 2,
                "opendata-open-data-policy-getting-org-approval": 2,
                "opendata-implementing-an-open-data-program-scraping-open-data": -1,
                "opendata-implementing-an-open-data-program-making-machine-readable": -1,
                "opendata-implementing-an-open-data-program-open-data-formats": -1,
                "opendata-implementing-an-open-data-program-open-data-license": -1,
                "opendata-implementing-an-open-data-program-open-data-standards": -1,
                "opendata-implementing-an-open-data-program-managing-open-data": -1,
                "opendata-implementing-an-open-data-program-frequency-of-release": -1,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": -1
            }.items()])

        self.sly_less = UserFactory.create(
            first_name=u"sly",
            last_name=u"stone-less-knowledgeable",
            email=u"sly@stone-less-knowledgeable.com",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-implementing-an-open-data-program-open-data-standards": -1,
                "opendata-implementing-an-open-data-program-managing-open-data": -1,
                "opendata-implementing-an-open-data-program-frequency-of-release": -1,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": -1
            }.items()])

        self.paul_lennon = UserFactory.create(
            first_name=u"paul",
            last_name=u"lennon",
            email=u"paul@lennon.com",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-open-data-policy-core-mission": 5,
                "opendata-open-data-policy-sensitive-vs-non-sensitive": 5,
                "opendata-open-data-policy-crafting-an-open-data-policy": 5,
                "opendata-open-data-policy-getting-public-input": 5,
                "opendata-open-data-policy-getting-org-approval": 5,
                "opendata-implementing-an-open-data-program-scraping-open-data": 5,
                "opendata-implementing-an-open-data-program-making-machine-readable": 5,
                "opendata-implementing-an-open-data-program-open-data-formats": 5,
                "opendata-implementing-an-open-data-program-open-data-license": 5,
                "opendata-implementing-an-open-data-program-open-data-standards": 5,
                "opendata-implementing-an-open-data-program-managing-open-data": 5,
                "opendata-implementing-an-open-data-program-frequency-of-release": 5,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": 5
            }.items()])

        self.dubya_shrub = UserFactory.create(
            first_name=u"dubya",
            last_name=u"shrub",
            email=u"dubya@shrub.com",
            connections=[], languages=[], expertise_domains=[],
            skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
                "opendata-open-data-policy-core-mission": 1,
                "opendata-open-data-policy-sensitive-vs-non-sensitive": 1,
                "opendata-open-data-policy-crafting-an-open-data-policy": 1,
                "opendata-open-data-policy-getting-public-input": 1,
                "opendata-open-data-policy-getting-org-approval": 1,
                "opendata-implementing-an-open-data-program-scraping-open-data": 1,
                "opendata-implementing-an-open-data-program-making-machine-readable": 1,
                "opendata-implementing-an-open-data-program-open-data-formats": 1,
                "opendata-implementing-an-open-data-program-open-data-license": 1,
                "opendata-implementing-an-open-data-program-open-data-standards": 1,
                "opendata-implementing-an-open-data-program-managing-open-data": 1,
                "opendata-implementing-an-open-data-program-frequency-of-release": 1,
                "opendata-implementing-an-open-data-program-data-quality-and-integrity": 1
            }.items()])
        db.session.commit()

    def test_get_most_complete_profiles_works(self):
        user_scores = models.User.get_most_complete_profiles()
        self.assertEqual(user_scores.all()[-1][0].email, self.sly_less.email)
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
        message1 = models.SharedMessageEvent.from_user(a, message=u"hi")
        message2 = models.SharedMessageEvent.from_user(other, message=u"other")
        db.session.add(message1)
        db.session.add(message2)
        db.session.commit()
        messages = models.Event.query_in_deployment()
        eq_(messages.count(), 1)
        eq_(messages[0].type, 'shared_message')
        eq_(messages[0].message, 'hi')
        eq_(messages[0].user.email, 'a@example.org')

class FullLocationDbTests(DbTestCase):
    def create_app(self):
        app = super(FullLocationDbTests, self).create_app()
        babel.init_app(app)
        return app

    def test_empty(self):
        user = models.User()
        eq_(user.full_location, '')

    def test_city_only(self):
        user = models.User()
        user.city = 'New York'
        eq_(user.full_location, 'New York')

    def test_country_is_zz(self):
        user = models.User()
        user.country = Country('ZZ')
        eq_(user.full_location, '')

    def test_city_and_country(self):
        user = models.User()
        user.city = 'New York'
        user.country = Country('US')
        eq_(user.full_location, 'New York, United States')

    def country_only(self):
        user = models.User()
        user.country = Country('US')
        eq_(user.full_location, 'United States')

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
        self.paul_lennon = UserFactory.create(
            first_name=u"paul",
            last_name=u"lennon",
            email=u"paul@lennon.com",
            connections=[], languages=[], expertise_domains=[], skills=[])

        self.dubya_shrub = UserFactory.create(
            first_name=u"dubya",
            last_name=u"shrub",
            email=u"dubya@shrub.com",
            connections=[], languages=[], expertise_domains=[], skills=[])

        self.sly_less = UserFactory.create(
            first_name=u"sly",
            last_name=u"stone-less-knowledgeable",
            email=u"sly@stone-less-knowledgeable.com",
            connections=[], languages=[], expertise_domains=[], skills=[])

        self.sly = UserFactory.create(
            first_name=u"sly",
            last_name=u"stone",
            email=u"sly@stone.com",
            connections=[], languages=[], expertise_domains=[], skills=[])

        db.session.commit()

    def test_creates_connection_event(self):
        '''
        Adding connections should create one event.
        '''
        dubya = self.dubya_shrub
        lennon = self.paul_lennon
        stone = self.sly
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
        self.paul_lennon = UserFactory.create(
            first_name=u"paul",
            last_name=u"lennon",
            email=u"paul@lennon.com",
            connections=[], languages=[], expertise_domains=[], skills=[])

        self.dubya_shrub = UserFactory.create(
            first_name=u"dubya",
            last_name=u"shrub",
            email=u"dubya@shrub.com",
            connections=[], languages=[], expertise_domains=[], skills=[])

        self.sly_less = UserFactory.create(
            first_name=u"sly",
            last_name=u"stone-less-knowledgeable",
            email=u"sly@stone-less-knowledgeable.com",
            connections=[], languages=[], expertise_domains=[], skills=[])

        self.sly = UserFactory.create(
            first_name=u"sly",
            last_name=u"stone",
            email=u"sly@stone.com",
            connections=[], languages=[], expertise_domains=[], skills=[])

        db.session.commit()

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

    def test_user_disconnect_on_sender_deletion(self):
        '''
        When a sender is deleted, their related connections disappear.
        '''

        self.sly_less.email_connect([self.dubya_shrub])
        db.session.commit()

        db.session.delete(self.sly_less)
        db.session.commit()
        self.assertEquals(self.dubya_shrub.connections, 0)

    def test_user_disconnect_on_recipient_deletion(self):
        '''
        When a recipient is deleted, their related connections disappear.
        '''

        self.sly_less.email_connect([self.dubya_shrub])
        db.session.commit()

        db.session.delete(self.dubya_shrub)
        db.session.commit()
        self.assertEquals(self.sly_less.connections, 0)

    def test_user_connect_on_email_several(self):
        '''
        A user gains several connections on emailing several people.
        '''
        dubya = self.dubya_shrub
        lennon = self.paul_lennon
        stone = self.sly
        self.sly_less.email_connect([dubya, lennon, stone])
        db.session.commit()
        self.assertEquals(self.sly_less.connections, 3)

    def test_user_connect_reciprocal(self):
        '''
        A user's connections are reciprocal.
        '''
        dubya = self.dubya_shrub
        lennon = self.paul_lennon
        stone = self.sly
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
        paul = self.paul_lennon
        for _ in xrange(0, 3):
            self.sly_less.email_connect([paul])
        db.session.commit()
        self.assertEquals(self.sly_less.connections, 1)

    def test_user_get_most_complete_profiles_works(self):
        '''
        Make sure the `get_most_complete_profiles` endpoint works.
        '''
        dubya = self.dubya_shrub
        lennon = self.paul_lennon
        stone = self.sly
        self.assertEquals(models.Email.query.count(), 0)
        self.assertEquals([(u.email, score) for u, score in models.User.get_most_connected_profiles()],
                          [])
        self.sly_less.email_connect([dubya, lennon, stone])
        lennon.email_connect([dubya])
        db.session.commit()
        self.assertEquals(models.Email.query.count(), 4)
        self.assertEquals([(u.email, score) for u, score in models.User.get_most_connected_profiles()],
                          [(self.sly_less.email, 3L),
                           (lennon.email, 2L),
                           (dubya.email, 2L),
                           (stone.email, 1L)])

def test_get_postgres_create_table_sql_does_not_explode():
    get_postgres_create_table_sql()
