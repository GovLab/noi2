import os
import requests
from flask.ext.script.commands import InvalidCommand, Command, Option
from flask_script import Manager

from ..models import User
from . import sso
from .config import config

DiscourseCommand = manager = Manager(usage='Manage Discourse integration.')

class CustomOriginCommand(Command):
    def __init__(self):
        super(CustomOriginCommand, self).__init__(self.run_command)
        self.option_list.append(Option(
            '--origin',
            dest='origin',
            help='Origin of NoI server (e.g. http://localhost:8080)'
        ))

    def get_origin(self, app, origin):
        if origin is None:
            if os.environ.get('NOI_DEPLOY') == 'production':
                origin = 'https://%s' % app.config['NOI_DEPLOY']
                print "Inferring server origin is %s." % origin
                print "If this is incorrect, please use the --origin option."
            else:
                raise InvalidCommand(
                    'Cannot determine origin of server; please provide one '
                    'with the --origin option.'
                )
        return origin

    def run_command(self):
        raise NotImplementedError()

    def __call__(self, app=None, *args, **kwargs):
        origin = self.get_origin(app, kwargs.get('origin'))
        if 'origin' in kwargs:
            del kwargs['origin']
        with app.test_request_context(base_url=origin):
            return self.run(*args, **kwargs)

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

class SyncUserCommand(CustomOriginCommand):
    def run_command(self, username):
        '''
        Sync Discourse SSO information about the given user.
        '''

        user = User.query_in_deployment().filter(User.username==username)[0]

        sync_user_with_discourse(user)

        print "User %s (%s) synchronized." % (user.username, user.full_name)

manager.add_command('sync_user', SyncUserCommand)
