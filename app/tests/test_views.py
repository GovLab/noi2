import re
import datetime
from StringIO import StringIO
from urllib import urlencode
from moto import mock_s3
import boto
from flask import url_for
from flask_login import current_user

from app import (QUESTIONS_BY_ID, MIN_QUESTIONS_TO_JOIN, LEVELS,
                 QUESTIONNAIRES_BY_ID, mail)
from app.views import views, get_best_registration_step_url
from app.models import User, SharedMessageEvent, ConnectionEvent, db

from .util import create_app
from .test_models import DbTestCase
from .factories import UserFactory, UserSkillFactory

LOGGED_IN_SENTINEL = '<a href="/logout"'

@views.route('/__blank')
def blank_page():
    '''
    This is just a really simple page to redirect fake users to after
    login; because the page takes so little time to render, it actually
    improves the speed of tests that require login.
    '''

    if current_user.is_authenticated():
        # Just make sure LOGGED_IN_SENTINEL is in the page.
        return '<a href="/logout">logout</a>'
    return ''

class ViewTestCase(DbTestCase):
    BASE_APP_CONFIG = DbTestCase.BASE_APP_CONFIG.copy()

    BASE_APP_CONFIG.update(
        DEBUG=False,
        WTF_CSRF_ENABLED=False,
        CACHE_NO_NULL_WARNING=True
    )

    def create_app(self):
        return create_app(config=self.BASE_APP_CONFIG.copy())

    def logout(self):
        res = self.client.get('/logout', follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL not in res.data
        return res

    def create_user(self, email, password, fully_register=True, **kwargs):
        if fully_register == False:
            kwargs['joined'] = None
        # These default to none
        for attr in ('position', 'organization',
                     'organization_type', 'country', 'city', 'projects'):
            kwargs[attr] = kwargs.get(attr)

        # These default ot empty list
        for attr in ('expertise_domains', 'languages', 'skills', 'connections', 'messages'):
            kwargs[attr] = kwargs.get(attr, [])

        user = UserFactory.create(email=email, password=password, **kwargs)
        self.last_created_user = user
        return user

    def login(self, email=None, password=None, fully_register=True, **kwargs):
        if email is None:
            email = u'test@example.org'
            password = 'test123'
            self.create_user(email=email, password=password,
                             fully_register=fully_register, **kwargs)
        res = self.client.post('/login', data=dict(
            next='/__blank',
            submit="Login",
            email=email,
            password=password
        ), follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL in res.data
        return res

    def assertRequiresLogin(self, path, method='get'):
        method = getattr(self.client, method)
        self.assertRedirects(method(path),
                             '/login?%s' % urlencode({'next': path}))


class EmailTestCase(ViewTestCase):
    BASE_APP_CONFIG = ViewTestCase.BASE_APP_CONFIG.copy()

    BASE_APP_CONFIG.update(
        MAIL_USERNAME='foo@noi.org',
        NOI_DEPLOY='noi.org',
        MAIL_SUPPRESS_SEND=True,
    )

    def register_and_login(self, username, password):
        res = self.client.post('/register', data=dict(
            next='/__blank',
            first_name=u'John',
            last_name=u'Doe',
            email=username,
            password=password,
            submit='Register'
        ), follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL in res.data
        return res


class InviteTests(EmailTestCase):
    def setUp(self):
        super(ViewTestCase, self).setUp()
        self.login()

    def test_get_is_ok(self):
        self.assert200(self.client.get('/invite'))

    def test_post_with_valid_email_sends_invite(self):
        with mail.record_messages() as outbox:
            res = self.client.post('/invite', data={
                'email': 'foo@example.org'
            }, follow_redirects=True)
            self.assertEqual(len(outbox), 1)
            msg = outbox[0]
            self.assertEqual(msg.sender, 'foo@noi.org')
            self.assertEqual(msg.recipients, ['foo@example.org'])
            assert 'https://noi.org' in msg.body
        self.assert200(res)
        assert 'Invitation sent!' in res.data

    def test_post_with_invalid_email_shows_error(self):
        with mail.record_messages() as outbox:
            res = self.client.post('/invite', data={
                'email': 'blarg'
            })
            self.assertEqual(len(outbox), 0)
        self.assert200(res)
        assert 'Invalid email address' in res.data
        assert 'Your form submission was invalid' in res.data


class RegistrationStepOneTests(EmailTestCase):
    def test_registration_complains_if_email_is_taken(self):
        self.register_and_login('foo@example.org', 'test123')
        self.logout()

        with mail.record_messages() as outbox:
            res = self.client.post('/register', data=dict(
                email=u'foo@example.org'
            ))
            self.assertEqual(len(outbox), 0)

        assert ('foo@example.org is already '
                'associated with an account') in res.data

    def test_registration_sends_email(self):
        with mail.record_messages() as outbox:
            self.register_and_login('foo@example.org', 'test123')

            self.assertEqual(len(outbox), 1)
            msg = outbox[0]
            self.assertEqual(msg.sender, 'noreply@networkofinnovators.org')
            self.assertEqual(msg.recipients, ['foo@example.org'])
            assert 'http://localhost/confirm/' in msg.body

    def test_registration_works(self):
        self.register_and_login('foo@example.org', 'test123')
        self.logout()
        self.login('foo@example.org', 'test123')


class RegistrationStepOnePointFiveTests(EmailTestCase):
    def setUp(self):
        super(EmailTestCase, self).setUp()
        self.login(fully_register=False, confirmed_at=None)
        self.user = self.last_created_user

    def test_redirects_to_activity_page_if_already_confirmed(self):
        self.user.confirmed_at = datetime.datetime.now()
        res = self.client.get('/register/step/1.5')
        self.assertRedirects(res, '/activity')

    def test_renders_ok_for_new_users(self):
        res = self.client.get('/register/step/1.5')
        self.assert200(res)
        self.assertContext('is_legacy_user', False)

    def test_renders_ok_for_legacy_users(self):
        self.user.position = 'Hamburger Salesperson'

        res = self.client.get('/register/step/1.5')
        self.assert200(res)
        assert 'confirm your e-mail address at test@example.org' in res.data
        self.assertContext('is_legacy_user', True)

    def test_sends_confirmation_email_on_post(self):
        with mail.record_messages() as outbox:
            res = self.client.post('/register/step/1.5')

            self.assertEqual(len(outbox), 1)
            msg = outbox[0]
            self.assertEqual(msg.sender, 'noreply@networkofinnovators.org')
            self.assertEqual(msg.recipients, ['test@example.org'])
            assert 'http://localhost/confirm/' in msg.body


class RegistrationStepsTwoAndThreeTests(ViewTestCase):
    OPENDATA_QUESTIONNAIRE = QUESTIONNAIRES_BY_ID['opendata']
    NUM_OPENDATA_QUESTIONS = len(OPENDATA_QUESTIONNAIRE['questions'])

    def setUp(self):
        super(RegistrationStepsTwoAndThreeTests, self).setUp()
        self.login(fully_register=False)

    def _get_best_step_url(self):
        return get_best_registration_step_url(self.last_created_user)

    def test_best_registration_step_is_2_by_default(self):
        self.assertEqual(self._get_best_step_url(), '/register/step/2')

    def test_best_registration_step_is_3_if_org_is_filled(self):
        self.last_created_user.organization = 'foo'
        self.assertEqual(self._get_best_step_url(), '/register/step/3')

    def test_best_registration_step_is_3_if_skills_exist(self):
        self.client.post('/register/step/3/opendata/1', data={
            'answer': '-1'
        })
        self.assertEqual(self._get_best_step_url(), '/register/step/3')

    def test_step_2_is_ok(self):
        res = self.client.get('/register/step/2')
        self.assert200(res)

    def test_step_2_redirects_to_step_3(self):
        self.assertRedirects(self.client.post('/register/step/2'),
                             '/register/step/3')

    def test_step_3_is_ok(self):
        res = self.client.get('/register/step/3')
        self.assert200(res)
        self.assertContext('user_can_join', False)

    def test_step_3_with_areaid_links_to_first_unanswered_question(self):
        res = self.client.get('/register/step/3/opendata')
        self.assert200(res)
        assert '/register/step/3/opendata/1' in res.data

    def test_step_3_with_questionid_is_ok(self):
        self.assert200(self.client.get('/register/step/3/opendata/1'))
        self.assert200(self.client.get('/register/step/3/opendata/%d' % (
            self.NUM_OPENDATA_QUESTIONS
        )))
        self.assertContext('user_can_join', False)

    def test_step_3_user_can_join_when_min_questions_are_answered(self):
        self.assertFalse(self.last_created_user.has_fully_registered)
        for i in range(1, MIN_QUESTIONS_TO_JOIN + 1):
            res = self.client.post('/register/step/3/opendata/%d' % i, data={
                'answer': '-1'
            })
            self.assertEqual(res.status_code, 302)
        self.client.get('/register/step/3')
        self.assertContext('user_can_join', True)
        self.assert200(self.client.get('/activity'))
        self.assertTrue(self.last_created_user.has_fully_registered)

    def test_step_3_answering_last_question_works(self):
        self.assertEqual(len(self.last_created_user.skills), 0)
        res = self.client.post('/register/step/3/opendata/%d' % (
            self.NUM_OPENDATA_QUESTIONS
        ), data={
            'answer': '-1'
        })
        self.assertRedirects(res, '/activity')
        self.assertEqual(len(self.last_created_user.skills), 1)

    def test_step_3_answering_first_question_works(self):
        self.assertEqual(len(self.last_created_user.skills), 0)
        res = self.client.post('/register/step/3/opendata/1', data={
            'answer': '-1'
        })
        self.assertRedirects(res, '/register/step/3/opendata/2')
        self.assertEqual(len(self.last_created_user.skills), 1)

    def test_step_3_with_invalid_questionid_is_not_found(self):
        self.assert404(self.client.get('/register/step/3/opendata/0'))
        self.assert404(self.client.get('/register/step/3/opendata/blah'))
        self.assert404(self.client.get('/register/step/3/opendata/%d' % (
            (self.NUM_OPENDATA_QUESTIONS + 1)
        )))

    def test_step_3_with_invalid_areaid_is_not_found(self):
        self.assert404(self.client.get('/register/step/3/blah'))
        self.assert404(self.client.get('/register/step/3/blah/1'))

class ActivityFeedTests(ViewTestCase):
    def test_anonymous_get_is_ok(self):
        self.assert200(self.client.get('/activity'))

    def test_authenticated_but_not_confirmed_get_is_redirected(self):
        self.login(confirmed_at=None)
        self.assertRedirects(self.client.get('/activity'),
                             '/register/step/1.5')

    def test_authenticated_but_not_fully_registered_get_is_redirected(self):
        self.login(fully_register=False)
        self.assertRedirects(self.client.get('/activity'),
                             '/register/step/2')

    def test_posting_activity_requires_login(self):
        res = self.client.post('/activity', data=dict(
            message=u"hello there"
        ), follow_redirects=True)
        self.assert200(res)
        self.assertEqual(SharedMessageEvent.query_in_deployment().count(), 0)
        assert 'You must log in to post a message' in res.data

    def test_posting_activity_requires_full_name(self):
        self.login(first_name=u'', last_name=u'')
        res = self.client.post('/activity', data=dict(
            message=u"hello there"
        ), follow_redirects=True)
        self.assert200(res)
        self.assertEqual(SharedMessageEvent.query_in_deployment().count(), 0)
        assert 'We need your name before you can post' in res.data

    def test_posting_activity_works(self):
        self.login()
        user = User.query_in_deployment()\
                 .filter(User.email == 'test@example.org').one()
        user.first_name = 'John'
        user.last_name = 'Doe'
        res = self.client.post('/activity', data=dict(
            message=u"hello there"
        ), follow_redirects=True)
        self.assert200(res)
        self.assertEqual(SharedMessageEvent.query_in_deployment().count(), 1)
        assert 'Message posted' in res.data
        assert 'hello there' in res.data

    def test_email_connection_is_activity(self):
        UserFactory.create(email=u'sly@stone.com', connections=[])
        self.login()
        res = self.client.post('/email', data={
            'emails[]': ['sly@stone.com']
        })
        self.assertEquals(res.status, '204 NO CONTENT')
        self.assertEqual(ConnectionEvent.query_in_deployment().count(), 1)

        res = self.client.get('/activity')
        self.assert200(res)
        assert '1 new connection made in NOI' in res.data
        assert '1 connection' in res.data

    def test_activity_is_ok(self):
        self.login()
        self.assert200(self.client.get('/activity'))

    def test_activity_page_with_negative_number_is_not_found(self):
        self.assert404(self.client.get('/activity/page/-1'))

    def test_activity_page_zero_is_not_found(self):
        self.assert404(self.client.get('/activity/page/0'))

    def test_activity_page_one_is_ok(self):
        self.assert200(self.client.get('/activity/page/1'))

    def test_activity_page_with_non_number_is_not_found(self):
        self.assert404(self.client.get('/activity/page/foo'))

    def test_activity_page_with_too_big_a_number_is_not_found(self):
        self.assert404(self.client.get('/activity/page/9999999'))

class MyProfileTests(ViewTestCase):
    def test_get_redirects_to_register_step_1_point_5_if_needed(self):
        self.login(fully_register=False, confirmed_at=None)
        self.assertRedirects(self.client.get('/me'), '/register/step/1.5')

    def test_get_redirects_to_register_step_2_if_needed(self):
        self.login(fully_register=False)
        self.assertRedirects(self.client.get('/me'), '/register/step/2')

    def test_get_is_ok(self):
        self.login()
        self.assert200(self.client.get('/me'))

    def test_invalid_form_shows_errors(self):
        self.login()
        res = self.client.post('/me', data={
            'first_name': '',
            'expertise_domain_names': 'Agriculture',
        })
        self.assertEqual(self.last_created_user.expertise_domain_names, [])
        assert "please correct errors" in res.data

    def test_updating_profile_with_username_works(self):
        self.login(username='bop')
        user = self.last_created_user
        res = self.client.post('/me', data={
            'first_name': 'John2',
            'last_name': 'Doe2',
            # Since the user has a username, there should be a username
            # field in the profile form, so providing a value for the
            # username should work.
            'username': 'blah',
        }, follow_redirects=True)
        assert 'Your profile has been saved' in res.data
        self.assert200(res)
        self.assertEqual(user.username, 'blah')

    def test_updating_profile_works(self):
        self.login()
        user = self.last_created_user
        res = self.client.post('/me', data={
            'first_name': 'John2',
            'last_name': 'Doe2',
            'expertise_domain_names': 'Agriculture',
            'locales': 'af',
            # The user doesn't have a username, so this shouldn't do
            # anything, as the profile field shouldn't have a username field.
            'username': 'blah',
        }, follow_redirects=True)
        assert 'Your profile has been saved' in res.data
        self.assert200(res)
        self.assertIsNone(user.username)
        self.assertEqual(user.first_name, 'John2')
        self.assertEqual(user.last_name, 'Doe2')
        self.assertEqual(user.expertise_domain_names, ['Agriculture'])
        self.assertEqual(len(user.locales), 1)
        self.assertEqual(str(user.locales[0]), 'af')

class MyExpertiseTests(ViewTestCase):
    OPENDATA_QUESTIONNAIRE = QUESTIONNAIRES_BY_ID['opendata']
    NUM_OPENDATA_QUESTIONS = len(OPENDATA_QUESTIONNAIRE['questions'])

    def setUp(self):
        super(MyExpertiseTests, self).setUp()
        self.login()

    def test_get_is_ok(self):
        self.assert200(self.client.get('/my-expertise/'))

    def test_with_areaid_and_no_skills_shows_into_text(self):
        res = self.client.get('/my-expertise/opendata')
        self.assert200(res)
        assert '/my-expertise/opendata/1#expertise' in res.data

    def test_with_areaid_and_skills_redirects_to_unanswered_question(self):
        self.client.post('/my-expertise/opendata/1', data={
            'answer': '-1'
        })
        self.assertRedirects(self.client.get('/my-expertise/opendata'),
                             '/my-expertise/opendata/2')

    def test_with_areaid_and_skills_redirects_to_last_question(self):
        for question in self.OPENDATA_QUESTIONNAIRE['questions']:
            self.last_created_user.set_skill(question['id'], -1)
        db.session.commit()
        self.assertRedirects(
            self.client.get('/my-expertise/opendata'),
            '/my-expertise/opendata/%d' % self.NUM_OPENDATA_QUESTIONS
        )

    def test_with_questionid_is_ok(self):
        self.assert200(self.client.get('/my-expertise/opendata/1'))
        self.assert200(self.client.get('/my-expertise/opendata/%d' % (
            self.NUM_OPENDATA_QUESTIONS
        )))

    def test_answering_last_question_works(self):
        self.assertEqual(len(self.last_created_user.skills), 0)
        res = self.client.post('/my-expertise/opendata/%d' % (
            self.NUM_OPENDATA_QUESTIONS
        ), data={
            'answer': '-1'
        })
        self.assertRedirects(res, '/my-expertise/')
        self.assertEqual(len(self.last_created_user.skills), 1)

    def test_answering_first_question_works(self):
        self.assertEqual(len(self.last_created_user.skills), 0)
        res = self.client.post('/my-expertise/opendata/1', data={
            'answer': '-1'
        })
        self.assertRedirects(res, '/my-expertise/opendata/2')
        self.assertEqual(len(self.last_created_user.skills), 1)

    def test_step_3_with_invalid_questionid_is_not_found(self):
        self.assert404(self.client.get('/my-expertise/opendata/0'))
        self.assert404(self.client.get('/my-expertise/opendata/blah'))
        self.assert404(self.client.get('/my-expertise/opendata/%d' % (
            (self.NUM_OPENDATA_QUESTIONS + 1)
        )))

    def test_step_3_with_invalid_areaid_is_not_found(self):
        self.assert404(self.client.get('/my-expertise/blah'))
        self.assert404(self.client.get('/my-expertise/blah/1'))

class MatchMeTests(ViewTestCase):
    def setUp(self):
        super(MatchMeTests, self).setUp()
        self.login()

        learn = LEVELS['LEVEL_I_WANT_TO_LEARN']['score']
        refer = LEVELS['LEVEL_I_CAN_REFER']['score']
        explain = LEVELS['LEVEL_I_CAN_EXPLAIN']['score']
        do_it = LEVELS['LEVEL_I_CAN_DO_IT']['score']

        skill = "opendata-open-data-policy-core-mission"

        self.last_created_user.set_skill(skill, learn)

        UserFactory.create(
            first_name=u"connector",
            last_name=u"stone",
            connections=[],
            skills=[UserSkillFactory.create(name=skill, level=refer)]
        )

        UserFactory.create(
            first_name=u"peer",
            last_name=u"stone",
            connections=[],
            skills=[UserSkillFactory.create(name=skill, level=learn)]
        )

        UserFactory.create(
            first_name=u"explainer",
            last_name=u"stone",
            connections=[],
            skills=[UserSkillFactory.create(name=skill, level=explain)]
        )

        UserFactory.create(
            first_name=u"practitioner",
            last_name=u"stone",
            connections=[],
            skills=[UserSkillFactory.create(name=skill, level=do_it)]
        )

        db.session.commit()

    def test_match_redirects_to_practitioners(self):
        self.assertRedirects(self.client.get('/match'),
                             '/match/practitioners')

    def test_connectors_is_ok(self):
        res = self.client.get('/match/connectors')
        self.assert200(res)
        assert 'connector stone' in res.data

    def test_peers_is_ok(self):
        res = self.client.get('/match/peers')
        self.assert200(res)
        assert 'peer stone' in res.data

    def test_explainers_is_ok(self):
        res = self.client.get('/match/explainers')
        self.assert200(res)
        assert 'explainer stone' in res.data

    def test_practitioners_is_ok(self):
        res = self.client.get('/match/practitioners')
        self.assert200(res)
        assert 'practitioner stone' in res.data

class EmailTests(ViewTestCase):
    def setUp(self):
        super(EmailTests, self).setUp()
        UserFactory.create(email=u'sly@stone.com', connections=[])
        self.login()

    def test_email_generates_connection_and_connection_event(self):
        res = self.client.post('/email', data={'emails[]': ['sly@stone.com']})
        self.assertEquals(res.status, '204 NO CONTENT')
        user = User.query_in_deployment()\
                 .filter(User.email==u'test@example.org').one()
        self.assertEquals(1, user.connections)

    def test_repeat_email_does_not_generate_connection_event(self):
        res = self.client.post('/email', data={'emails[]': ['sly@stone.com']})
        self.assertEquals(res.status, '204 NO CONTENT')
        self.assertEqual(ConnectionEvent.query_in_deployment().count(), 1)
        res = self.client.post('/email', data={'emails[]': ['sly@stone.com']})
        self.assertEquals(res.status, '204 NO CONTENT')
        self.assertEqual(ConnectionEvent.query_in_deployment().count(), 1)

    def test_email_with_multiple_emails_is_not_implemented(self):
        UserFactory.create(email=u'paul@lennon.com')
        res = self.client.post('/email', data={
            'emails[]': ['sly@stone.com', 'paul@lennon.com']
        })
        self.assertEquals(res.status, '501 NOT IMPLEMENTED')


class SearchTests(ViewTestCase):
    def setUp(self):
        super(SearchTests, self).setUp()
        self.login()

        UserFactory.create(
            first_name=u"practitioner",
            last_name=u"stone",
            connections=[],
            languages=['en'],
            expertise_domains=['Labor'],
            country='US',
            skills=[UserSkillFactory.create(
                name="opendata-open-data-policy-core-mission",
                level=LEVELS['LEVEL_I_CAN_DO_IT']['score']
            )]
        )

        UserFactory.create(
            first_name=u"somebody",
            last_name=u"else",
            connections=[],
            languages=['es'],
            expertise_domains=['Agriculture'],
            country='CA',
            skills=[]
        )

        db.session.commit()

    def test_get_is_ok(self):
        res = self.client.get('/search')
        self.assert200(res)
        assert "Find Innovator" in res.data

    def test_results_is_ok(self):
        res = self.client.get('/search?country=ZZ')
        self.assert200(res)
        assert "e-results-container" in res.data

    def test_expertise_search_contains_practitioners(self):
        res = self.client.get('/search?country=ZZ&questionnaire_area=opendata')
        self.assert200(res)
        assert "practitioner stone" in res.data
        assert "somebody else" not in res.data

    def test_country_search_works(self):
        res = self.client.get('/search?country=US')
        self.assert200(res)
        assert "practitioner stone" in res.data
        assert "somebody else" not in res.data

    def test_locale_search_works(self):
        res = self.client.get('/search?country=ZZ&locale=en')
        self.assert200(res)
        assert "practitioner stone" in res.data
        assert "somebody else" not in res.data

    def test_expertise_domain_search_works(self):
        res = self.client.get('/search?country=ZZ&expertise_domain_name=Labor')
        self.assert200(res)
        assert "practitioner stone" in res.data
        assert "somebody else" not in res.data

    def test_fulltext_search_finds_last_name(self):
        res = self.client.get('/search?country=ZZ&fulltext=practitioner')
        self.assert200(res)
        assert "practitioner stone" in res.data
        assert "somebody else" not in res.data

    def test_fulltext_search_finds_full_name(self):
        res = self.client.get('/search?country=ZZ&fulltext='
                              'practitioner+stone')
        self.assert200(res)
        assert "practitioner stone" in res.data
        assert "somebody else" not in res.data


class UploadPictureTests(ViewTestCase):
    BASE_APP_CONFIG = ViewTestCase.BASE_APP_CONFIG.copy()

    BASE_APP_CONFIG.update(
        S3_ACCESS_KEY_ID='my_access_key',
        S3_SECRET_ACCESS_KEY='my_secret_access_key',
        S3_BUCKET_NAME='my_bucket'
    )

    def setUp(self):
        super(UploadPictureTests, self).setUp()
        self.login()
        self.picture_path = self.last_created_user.picture_path

    def init_s3(self):
        self.conn = boto.connect_s3()
        self.bucket = self.conn.create_bucket('my_bucket')

    def test_invalid_form_is_bad_request(self):
        res = self.client.post('/me/picture')
        self.assert400(res)

    @mock_s3
    def test_remove_picture_works_if_picture_does_not_exist(self):
        self.init_s3()
        res = self.client.post('/me/picture/remove')
        self.assertEqual(res.status_code, 204)
        self.assertIsNone(self.bucket.get_key(self.picture_path))

    @mock_s3
    def test_remove_picture_works_if_picture_exists(self):
        self.init_s3()

        self.last_created_user.has_picture = True
        k = self.bucket.new_key(self.picture_path)
        k.set_contents_from_string('hi')

        res = self.client.post('/me/picture/remove')
        self.assertEqual(res.status_code, 204)
        self.assertIsNone(self.bucket.get_key(self.picture_path))
        self.assertFalse(self.last_created_user.has_picture)

    @mock_s3
    def test_valid_form_sets_picture(self):
        self.init_s3()
        res = self.client.post(
            '/me/picture',
            data={
                'picture': (StringIO('hi'), 'me.png')
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(res.status_code, 204)

        key = self.bucket.get_key(self.picture_path)
        self.assertEqual(key.get_contents_as_string(), 'hi')
        self.assertEqual(key.content_type, 'image/png')


class EmailConfirmationTests(EmailTestCase):
    def test_confirmation_works(self):
        self.register_and_login('foo@example.org', 'test123')

        with mail.record_messages() as outbox:
            res = self.client.post('/confirm', data=dict(
                email=u'foo@example.org'
            ))
            self.assertEqual(len(outbox), 1)
            msg = outbox[0]
            self.assertEqual(msg.sender, 'noreply@networkofinnovators.org')
            self.assertEqual(msg.recipients, ['foo@example.org'])
            assert 'http://localhost/confirm/' in msg.body
            assert ('Confirmation instructions have been '
                    'sent to foo@example.org') in res.data

        token = re.search(
            r'http:\/\/localhost\/confirm\/(.+)',
            msg.body,
            flags=re.MULTILINE
        ).group(1)

        res = self.client.get('/confirm/%s' % token)
        self.assertRedirects(res, '/activity')

        res = self.client.get('/activity')
        self.assertRedirects(res, '/register/step/2')

        res = self.client.get('/register/step/2')
        self.assert200(res)

        assert 'Your email has been confirmed' in res.data

class ViewTests(ViewTestCase):
    def test_security_post_views_exist(self):
        view_names = [
            self.app.config['SECURITY_POST_REGISTER_VIEW'],
            self.app.config['SECURITY_POST_CONFIRM_VIEW'],
            self.app.config['SECURITY_POST_LOGIN_VIEW'],
        ]
        for view_name in view_names:
            url_for(view_name)

    def test_main_page_is_ok(self):
        self.assert200(self.client.get('/'))

    def test_changing_locale_to_invalid_is_bad_request(self):
        res = self.client.post('/change-locale', data={
            'locale': 'lol'
        })
        self.assert400(res)

    def test_changing_locale_works(self):
        res = self.client.post('/change-locale', data={
            'locale': 'es'
        }, follow_redirects=True)
        self.assert200(res)
        assert '<html lang="es"' in res.data

    def test_about_page_is_ok(self):
        self.assert200(self.client.get('/about'))

    def test_terms_and_conditions_is_ok(self):
        self.assert200(self.client.get('/terms'))

    def test_faq_is_ok(self):
        self.assert200(self.client.get('/faq'))

    def test_feedback_page_is_ok(self):
        self.assert200(self.client.get('/feedback'))

    def test_nonexistent_page_is_not_found(self):
        self.assert404(self.client.get('/nonexistent'))

    def test_existing_user_profile_is_ok(self):
        u = self.create_user(email=u'u@example.org', password='t')
        self.login('u@example.org', 't')
        self.assert200(self.client.get('/user/%d' % u.id))

    def test_nonexistent_user_profile_is_not_found(self):
        self.login()
        self.assert404(self.client.get('/user/1234'))

    def test_settings_is_ok(self):
        self.login()
        res = self.client.get('/settings')
        self.assert200(res)

    def test_network_is_ok(self):
        self.login()
        res = self.client.get('/network')
        self.assert200(res)

    def test_user_profiles_require_login(self):
        self.assertRequiresLogin('/user/1234')

    def test_empty_match_results_are_ok(self):
        self.login()
        res = self.client.get('/match/connectors')
        self.assert200(res)
        assert 'You currently have no matches' in res.data
