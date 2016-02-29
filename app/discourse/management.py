import os
import sys
import json
from flask.ext.script.commands import InvalidCommand, Command, Option
from flask_script import Manager

from ..models import User
from . import sso, api
from .config import config

DiscourseCommand = manager = Manager(usage='Manage Discourse integration.')

class CustomOriginCommand(Command):
    def __init__(self, *args, **kwargs):
        super(CustomOriginCommand, self).__init__(*args, **kwargs)
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

    def __call__(self, app=None, *args, **kwargs):
        origin = self.get_origin(app, kwargs.get('origin'))
        if 'origin' in kwargs:
            del kwargs['origin']
        with app.test_request_context(base_url=origin):
            return self.run(*args, **kwargs)

def get_user_by_username(username):
    users = User.query_in_deployment().filter(User.username==username)

    if not users:
        raise InvalidCommand('Unable to find username %s.' % username)

    return users[0]

@manager.command
def http_get(path, username=None):
    '''
    Perform a HTTP GET using the Discourse API.

    For more information, see:

    https://meta.discourse.org/t/discourse-api-documentation/22706/1
    '''

    req = api.get(path, username=username)
    if req.status_code != 200:
        req.raise_for_status()

    sys.stdout.write(json.dumps(req.json(), indent=2))

@manager.command
def logout_user(username):
    '''
    Logout a user from Discourse.
    '''

    user = get_user_by_username(username)

    sso.logout_user(user)

    print "User %s (%s) logged out." % (user.username, user.full_name)

class SyncUserCommand(CustomOriginCommand):
    option_list = [
        Option('username', help='Username to sync with Discourse'),
        Option('-a', '--avatar-force-update',
               help='Force update of avatar image',
               action='store_true', default=False)
    ]

    def run(self, username, avatar_force_update):
        '''
        Sync Discourse SSO information about the given user.
        '''

        user = get_user_by_username(username)

        sso.sync_user(user, avatar_force_update=avatar_force_update)

        print "User %s (%s) synchronized." % (user.username, user.full_name)

manager.add_command('sync_user', SyncUserCommand)
