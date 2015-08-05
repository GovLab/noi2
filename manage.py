'''
NoI manage.py

Scripts to run the server and perform maintenance operations
'''

from app import mail, models
from app.factory import create_app
from app.models import db

from flask_migrate import Migrate
from flask_script import Manager

import subprocess

app = create_app() #pylint: disable=invalid-name
migrate = Migrate(app, db) #pylint: disable=invalid-name

manager = Manager(app) #pylint: disable=invalid-name

#manager.add_command('db', MigrateCommand)
#manager.add_command("assets", ManageAssets)


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
def drop_and_create_db(verbose=False):
    """
    Drops database and creates a new one
    """
    if not verbose:
        db.engine.echo = False
    db.reflect()
    db.drop_all()
    db.create_all()
    return 0


if __name__ == '__main__':
    subprocess.call('../symlink-hooks.sh', shell=True)
    manager.run()
