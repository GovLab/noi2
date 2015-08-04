'''
NoI manage.py

Scripts to run the server and perform maintenance operations
'''

from app import mail, models
from app.factory import create_app
from app.models import db

from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager

import subprocess
import sys

app = create_app()
migrate = Migrate(app, db)

manager = Manager(app)
#manager.add_command('db', MigrateCommand)
#manager.add_command("assets", ManageAssets)


@manager.shell
def _make_context():
    return dict(app=app, db=db, mail=mail, models=models)


@manager.command
@manager.option('-v', '--verbose', dest='verbose', default=False)
def drop_and_create_db(verbose=False):
    """
    Drops database and creates a new one
    """
    if not verbose:
        db.engine.echo = False
    db.drop_all()
    db.create_all()
    return 0


@manager.command
@manager.option('-v', '--verbose', dest='verbose', default=False)
def populate_db(verbose=False):
    from alphaworks.manage_helpers.populate_db import populate
    if not verbose:
        db.engine.echo = False

    sys.stdout.write(u'Populating database with seed data.\n')

    populate()
    return 0


if __name__ == '__main__':
    subprocess.call('../symlink-hooks.sh', shell=True)
    manager.run()
