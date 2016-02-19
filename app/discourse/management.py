import requests
from flask_script import Manager

from ..models import User
from . import sso
from .config import config

DiscourseCommand = manager = Manager(usage='Manage Discourse integration.')

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

@manager.command
def sync_user(username):
    '''
    Sync Discourse SSO information about the given user.
    '''

    user = User.query_in_deployment().filter(User.username==username)[0]

    r = requests.post(
        config.url("/admin/users/sync_sso"),
        params=dict(api_key=config.api_key,
                    api_username=config.admin_username),
        data=sso.user_info_qs(user, nonce='does not matter')
    )
    if r.status_code != 200:
        r.raise_for_status()

    print "User %s (%s) synchronized." % (user.username, user.full_name)
