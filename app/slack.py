import requests
from flask import current_app, url_for
from flask_script import Manager
from flask_security.signals import user_registered

from signals import user_changed_profile, user_completed_registration

def init_app(app):
    assert 'SLACK_WEBHOOK_URL' in app.config

    @user_registered.connect_via(app)
    def when_user_registered(sender, user, confirm_token, **extra):
        post_user_message(user, 'just registered.')

    @user_changed_profile.connect_via(app)
    def when_user_changed_profile(sender, user, avatar_changed=False, **extra):
        text = 'changed their profile.'
        if avatar_changed:
            text = 'changed their avatar.'
        post_user_message(user, text)

    @user_completed_registration.connect_via(app)
    def when_user_completed_registration(sender, user, **extra):
        post_user_message(user, ', ' + user.position + ' of ' + user.organization + ' just completed a new profile.')

def post_user_message(user, text):
    url = url_for('views.get_user', userid=user.id, _external=True)
    post_message(u'<%s|%s> %s' % (url, user.full_name, text))

def post_message(text):
    res = requests.post(
        current_app.config['SLACK_WEBHOOK_URL'],
        json={'text': text}
    )
    if res.status_code != 200:
        return res.raise_for_status()

SlackCommand = manager = Manager(usage='Manage Slack integration.')

@manager.command
def post(text='Hello! This is just a message to test slack integration.'):
    '''
    Post a message with the given optional text.
    '''

    post_message(text)
