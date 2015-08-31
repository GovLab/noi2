'''
NoI manage.py

Scripts to run the server and perform maintenance operations
'''

from app import mail, models
from app.factory import create_app
from app.models import db, User, UserSkill
from app.utils import csv_reader

from flask_alchemydumps import AlchemyDumps, AlchemyDumpsCommand
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_security.utils import encrypt_password
from flask_security.recoverable import send_reset_password_instructions

from random import choice
from sqlalchemy.exc import IntegrityError

import json
import os
import string
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
    subprocess.check_call(
        'pybabel extract -F app/babel.cfg -k lazy_gettext -o app/messages.pot app/',
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
def add_fake_users(users_csv):
    """
    Add a bunch of fake users from a CSV.  Will set bogus passwords for them.
    """
    # TODO make sure each fake user is pre- confirmed, otherwise the password
    # reset link we send them will require an email confirmation after the fact,
    # confusing
    # TODO add an auto-added flag (source)
    for row in csv_reader(os.path.join('/noi', users_csv)):
        row['password'] = ''.join(choice(string.letters + string.digits) for _ in range(20))
        row['active'] = False  # TODO is this OK?
        user = User(**row)  # pylint: disable=star-args
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            app.logger.warn('Could not add user with email "%s", as they are '
                            'already in the database.', row['email'])


@manager.command
def send_bulk_password_reset_links(users_csv):
    """
    Send bulk password reset links for the included emails.  Argument is a CSV,
    which will be read for an email column.
    """
    for row in csv_reader(os.path.join('/noi', users_csv)):
        # TODO filter users we don't have in the DB
        # TODO Make sure we only send bulk password resets to inactive users
        # who have never confirmed their email (even better would be to add an
        # auto-added flag and only send to those, then mark that we've sent
        # them a reset link)
        # TODO specialize the email sent so it's not "reset your password" but
        # "Claim your NoI account" or somesuch, upon which password is set.
        user = User.query.filter_by(email=row['email']).one()
        send_reset_password_instructions(user)


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
            skill = UserSkill(name=name, level=level)
            user.skills.append(skill)
            db.session.add(skill)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            app.logger.debug("Could not add user %s", user_data['email'])
            db.session.rollback()
    return 0



if __name__ == '__main__':
    subprocess.call('../symlink-hooks.sh', shell=True)
    manager.run()
