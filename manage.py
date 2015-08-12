'''
NoI manage.py

Scripts to run the server and perform maintenance operations
'''

from app import mail, models
from app.factory import create_app
from app.models import db, User, UserSkill

from flask_alchemydumps import AlchemyDumps, AlchemyDumpsCommand
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_security.utils import encrypt_password

import json
import subprocess

app = create_app() #pylint: disable=invalid-name
migrate = Migrate(app, db) #pylint: disable=invalid-name

manager = Manager(app) #pylint: disable=invalid-name

manager.add_command('db', MigrateCommand)
#manager.add_command("assets", ManageAssets)

alchemydumps = AlchemyDumps(app, db)
manager.add_command('alchemydumps', AlchemyDumpsCommand)


@manager.shell
def _make_context():
    '''
    Add certain variables to context for shell
    '''
    return dict(app=app, db=db, mail=mail, models=models)


@manager.command
def translate():
    """
    Extract translation
    """
    subprocess.check_call('pybabel extract -F app/babel.cfg -k lazy_gettext -o app/messages.pot app/',
                          shell=True)
    return 0


@manager.command
@manager.option('-v', '--verbose', dest='verbose', default=False)
def drop_db(verbose=False):
    """
    Drops database
    """
    if verbose:
        db.engine.echo = False
    else:
        db.engine.echo = True

    db.session.commit()
    db.reflect()
    db.drop_all()
    #db.engine.execute("drop schema if exists public cascade;")
    #db.engine.execute("create schema public;")
    #db.create_all()
    return 0


@manager.command
def populate_db():
    """
    Populate DB from fixture data
    """
    fixture_data = json.load(open('/noi/fixtures/sample_users.json', 'r'))
    for i, user_data in enumerate(fixture_data):
        skills = user_data.pop('skills')
        user = User(password=encrypt_password('foobar'), active=True, **user_data)
        for name, level in skills.iteritems():
            db.session.add(UserSkill(user_id=i+1, name=name, level=level))
        db.session.add(user)
    db.session.commit()
    return 0



if __name__ == '__main__':
    subprocess.call('../symlink-hooks.sh', shell=True)
    manager.run()
