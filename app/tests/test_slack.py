from flask import Flask
import mock
import flask_testing
from flask_security.signals import user_registered

from ..signals import user_changed_profile
from .test_views import ViewTestCase
from .. import slack

class SlackTestCase(flask_testing.TestCase):
    def create_app(self):
        app = Flask('slack_test')
        app.config['SLACK_WEBHOOK_URL'] = 'http://slack/123'
        slack.init_app(app)
        return app

@mock.patch('app.slack.post_user_message')
class SignalTests(SlackTestCase):
    def test_user_changed_avatar(self, post_user_message):
        user_changed_profile.send(self.app, user='user', avatar_changed=True)
        post_user_message.assert_called_with('user', 'changed their avatar.')

    def test_user_changed_profile(self, post_user_message):
        user_changed_profile.send(self.app, user='user', avatar_changed=False)
        post_user_message.assert_called_with('user', 'changed their profile.')

    def test_user_registered(self, post_user_message):
        user_registered.send(self.app, user='user', confirm_token='blah')
        post_user_message.assert_called_with('user', 'just registered.')

@mock.patch('requests.post')
class PostMessageTests(SlackTestCase):
    def test_it_works(self, post):
        post.return_value.status_code = 200

        slack.post_message('hi')

        post.assert_called_once_with('http://slack/123', json={'text': 'hi'})
        post.return_value.raise_for_status.assert_not_called()

    def test_it_raises_exception_when_not_ok(self, post):
        post.return_value.status_code = 500

        slack.post_message('hi')

        post.assert_called_once_with('http://slack/123', json={'text': 'hi'})
        post.return_value.raise_for_status.assert_called_once_with()

@mock.patch('app.slack.post_message')
class PostUserMessageTests(ViewTestCase):
    def test_it_works(self, post_message):
        self.login(first_name='Boop', last_name='Jones')
        user = self.last_created_user
        slack.post_user_message(user, 'is cool')
        post_message.assert_called_once_with(
            u'<http://localhost/user/%d|Boop Jones> is cool' % user.id
        )
