from app import QUESTIONS_BY_ID, MIN_QUESTIONS_TO_JOIN
from app.factory import create_app
from app.views import get_area_questionnaire_or_404
from app.models import User, SharedMessageEvent, ConnectionEvent

from .test_models import DbTestCase
from .util import load_fixture

LOGGED_IN_SENTINEL = '<a href="/me"'

class ViewTestCase(DbTestCase):
    def create_app(self):
        config = self.BASE_APP_CONFIG.copy()
        config.update(
            DEBUG=False,
            WTF_CSRF_ENABLED=False,
            # This speeds tests up considerably.
            SECURITY_PASSWORD_HASH='plaintext',
            CACHE_NO_NULL_WARNING=True,
        )
        return create_app(config=config)

    def register_and_login(self, username, password):
        res = self.client.post('/register', data=dict(
            next='/',
            first_name='John',
            last_name='Doe',
            email=username,
            password=password,
            submit='Register'
        ), follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL in res.data
        return res

    def logout(self):
        res = self.client.get('/logout', follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL not in res.data
        return res

    def create_user(self, email, password, fully_register=True):
        datastore = self.app.extensions['security'].datastore
        user = datastore.create_user(email=email, password=password)
        if fully_register:
            user.set_fully_registered()
        self.last_created_user = user
        return user

    def login(self, email=None, password=None, fully_register=True):
        if email is None:
            email = u'test@example.org'
            password = 'test123'
            self.create_user(email=email, password=password,
                             fully_register=fully_register)
        res = self.client.post('/login', data=dict(
            next='/',
            submit="Login",
            email=email,
            password=password
        ), follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL in res.data
        return res

class MultiStepRegistrationTests(ViewTestCase):
    OPENDATA_QUESTIONNAIRE = get_area_questionnaire_or_404('opendata')
    NUM_OPENDATA_QUESTIONS = len(OPENDATA_QUESTIONNAIRE['questions'])

    def setUp(self):
        super(MultiStepRegistrationTests, self).setUp()
        self.login(fully_register=False)

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

    def test_step_3_with_areaid_redirects_to_first_unanswered_question(self):
        self.assertRedirects(self.client.get('/register/step/3/opendata'),
                             '/register/step/3/opendata/1')

        self.client.post('/register/step/3/opendata/1', data={
            'answer': '-1'
        })
        self.assertRedirects(self.client.get('/register/step/3/opendata'),
                             '/register/step/3/opendata/2')

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
        self.assertRedirects(res, '/register/step/3')
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
    def test_viewing_activity_requires_full_registration(self):
        self.login(fully_register=False)
        self.assertRedirects(self.client.get('/activity'), '/register/step/2')

    def test_posting_activity_requires_full_name(self):
        self.login()
        res = self.client.post('/activity', data=dict(
            message="hello there"
        ), follow_redirects=True)
        self.assert200(res)
        self.assertEqual(SharedMessageEvent.query_in_deployment().count(), 0)
        assert 'We need your name before you can post' in res.data

    def test_posting_activity_works(self):
        self.login()
        user = User.query_in_deployment()\
                 .filter(User.email=='test@example.org').one()
        user.first_name = 'John'
        user.last_name = 'Doe'
        res = self.client.post('/activity', data=dict(
            message="hello there"
        ), follow_redirects=True)
        self.assert200(res)
        self.assertEqual(SharedMessageEvent.query_in_deployment().count(), 1)
        assert 'Message posted' in res.data
        assert 'hello there' in res.data

    def test_email_connection_is_activity(self):
        load_fixture()
        self.login()
        res = self.client.post('/email', data={
            'emails[]': ['sly@stone.com', 'paul@lennon.com']
        })
        self.assertEquals(res.status, '204 NO CONTENT')
        self.assertEqual(ConnectionEvent.query_in_deployment().count(), 1)

        res = self.client.get('/activity')
        self.assert200(res)
        assert '2 new connections made in NOI' in res.data
        assert '2 connections' in res.data

    def test_activity_is_ok(self):
        self.login()
        self.assert200(self.client.get('/activity'))

class MyProfileTests(ViewTestCase):
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

    def test_updating_profile_works(self):
        self.login()
        user = self.last_created_user
        res = self.client.post('/me', data={
            'first_name': 'John2',
            'last_name': 'Doe2',
            'expertise_domain_names': 'Agriculture',
            'locales': 'af'
        }, follow_redirects=True)
        assert 'Your profile has been saved' in res.data
        self.assert200(res)
        self.assertEqual(user.first_name, 'John2')
        self.assertEqual(user.last_name, 'Doe2')
        self.assertEqual(user.expertise_domain_names, ['Agriculture'])
        self.assertEqual(len(user.locales), 1)
        self.assertEqual(str(user.locales[0]), 'af')

class MyExpertiseTests(ViewTestCase):
    def setUp(self):
        super(MyExpertiseTests, self).setUp()
        self.question_id_0 = QUESTIONS_BY_ID.keys()[0]
        self.question_id_1 = QUESTIONS_BY_ID.keys()[1]

    def test_get_is_ok(self):
        self.login()
        self.assert200(self.client.get('/my-expertise'))

    def test_updating_expertise_works(self):
        self.login()
        user = self.last_created_user
        self.assertEqual(user.skill_levels, {})
        res = self.client.post('/my-expertise', data={
            self.question_id_0: '-1',
            self.question_id_1: 'invalid value',
            'invalid_question_id': '-1'
        })
        self.assert200(res)
        self.assertEqual(user.skill_levels, {
            self.question_id_0: -1
        })

class ViewTests(ViewTestCase):
    def test_main_page_is_ok(self):
        self.assert200(self.client.get('/'))

    def test_about_page_is_ok(self):
        self.assert200(self.client.get('/about'))

    def test_feedback_page_is_ok(self):
        self.assert200(self.client.get('/feedback'))

    def test_nonexistent_page_is_not_found(self):
        self.assert404(self.client.get('/nonexistent'))

    def test_registration_complains_if_email_is_taken(self):
        self.register_and_login('foo@example.org', 'test123')
        self.logout()
        res = self.client.post('/register', data=dict(
            email='foo@example.org'
        ))
        assert ('foo@example.org is already '
                'associated with an account') in res.data

    def test_registration_works(self):
        self.register_and_login('foo@example.org', 'test123')
        self.logout()
        self.login('foo@example.org', 'test123')

    def test_existing_user_profile_is_ok(self):
        u = self.create_user(email=u'u@example.org', password='t')
        self.login('u@example.org', 't')
        self.assert200(self.client.get('/user/%d' % u.id))

    def test_nonexistent_user_profile_is_not_found(self):
        self.login()
        self.assert404(self.client.get('/user/1234'))

    def test_search_is_ok(self):
        self.login()
        res = self.client.get('/search')
        self.assert200(res)
        assert "Search for Innovators" in res.data

    def test_search_results_is_ok(self):
        self.login()
        res = self.client.get('/search?country=ZZ')
        self.assert200(res)
        assert "Expertise search" in res.data

    def test_recent_users_is_ok(self):
        self.login()
        self.assert200(self.client.get('/users/recent'))

    def test_user_profiles_require_login(self):
        self.assertRedirects(self.client.get('/user/1234'),
                             '/login?next=%2Fuser%2F1234')

    def test_email(self):
        load_fixture()
        self.login()
        res = self.client.post('/email', data={
            'emails[]': ['sly@stone.com', 'paul@lennon.com']
        })
        self.assertEquals(res.status, '204 NO CONTENT')
        user = User.query_in_deployment()\
                 .filter(User.email=='test@example.org').one()
        self.assertEquals(2, user.connections)
