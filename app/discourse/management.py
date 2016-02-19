import requests
from flask_script import Manager

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
def test(username):
    '''
    Test Discourse integration.
    '''

    get_categories(username)
    print "Discourse integration works for user %s!" % username
