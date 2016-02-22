import os
import requests
from flask import current_app
from flask.ext.script.commands import InvalidCommand
from flask_script import Manager

from ..models import User
from . import sso
from .config import config

DiscourseCommand = manager = Manager(usage='Manage Discourse integration.')

def uses_custom_request_origin(func):
    return manager.option(
        '--origin',
        dest='origin',
        help='Origin of NoI server (e.g. http://localhost:8080)'
    )(func)

def custom_request_origin(kwargs):
    origin = kwargs.get('origin')
    if origin is None:
        if os.environ.get('NOI_DEPLOY') == 'production':
            origin = 'https://%s' % current_app.config['NOI_DEPLOY']
            print "Inferring server origin is %s." % origin
            print "If this is incorrect, please use the --origin option."
        else:
            raise InvalidCommand(
                'Cannot determine origin of server; please provide one '
                'with the --origin option.'
            )

    return current_app.test_request_context(base_url=origin)

def sync_user_with_discourse(user):
    r = requests.post(
        config.url("/admin/users/sync_sso"),
        params=dict(api_key=config.api_key,
                    api_username=config.admin_username),
        data=sso.user_info_qs(user, nonce='does not matter')
    )
    if r.status_code != 200:
        r.raise_for_status()

def get_categories(username):
    r = requests.get(config.url("/categories.json"), params=dict(
        api_key=config.api_key,
        api_username=username
    ))
    if r.status_code != 200:
        r.raise_for_status()
    return r.json()

@manager.command
def test_api():
    '''
    Test Discourse API integration.
    '''

    get_categories(config.admin_username)
    print "Discourse integration works!"

@uses_custom_request_origin
@manager.command
def sync_user(username, **kwargs):
    '''
    Sync Discourse SSO information about the given user.
    '''

    user = User.query_in_deployment().filter(User.username==username)[0]

    with custom_request_origin(kwargs):
        sync_user_with_discourse(user)

    print "User %s (%s) synchronized." % (user.username, user.full_name)
