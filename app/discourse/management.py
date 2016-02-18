import requests
from flask import current_app
from flask_script import Manager

DiscourseCommand = manager = Manager(usage='Manage Discourse integration.')

def get_categories(username):
    config = current_app.config['DISCOURSE']
    r = requests.get("%(origin)s/categories.json" % config, params=dict(
        api_key=config['api_key'],
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
