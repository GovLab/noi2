'''
NoI manage.py

Scripts to run the server and perform maintenance operations
'''

from app import mail, models, LEVELS, ORG_TYPES
from app.factory import create_app
from app.models import db, User, UserSkill
from app.utils import csv_reader

from flask_alchemydumps import AlchemyDumps, AlchemyDumpsCommand
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_security.utils import encrypt_password
from flask_security.recoverable import send_reset_password_instructions

from random import choice
from sqlalchemy.exc import IntegrityError, OperationalError

import codecs
import json
import os
import string
import subprocess
import yaml


app = create_app() #pylint: disable=invalid-name
migrate = Migrate(app, db) #pylint: disable=invalid-name

manager = Manager(app) #pylint: disable=invalid-name

manager.add_command('db', MigrateCommand)
#manager.add_command("assets", ManageAssets)

alchemydumps = AlchemyDumps(app, db)
manager.add_command('alchemydumps', AlchemyDumpsCommand)


def gettext_for(text):
    '''
    Generate a jinja2 "{{ gettext() }}" line for text.
    '''
    return u'{{{{ gettext("{}") }}}}\n'.format(text.replace('"', r'\"'))


@manager.shell
def _make_context():
    '''
    Add certain variables to context for shell
    '''
    return dict(app=app, db=db, mail=mail, models=models)


@manager.command
def translate_compile():
    """
    Compile existing .po files.  Since we don't keep the .mo files in version
    control, this has to be done before server start.
    """
    locales = set()
    with open('/noi/app/data/deployments.yaml') as deployments_file:
        deployments = yaml.load(deployments_file)

    for deployment in deployments.values():
        if 'locale' in deployment:
            locales.add(deployment['locale'])

    for locale in locales:
        subprocess.check_call('pybabel compile -f -l {locale} -d /noi/app/translations/'.format(
            locale=locale), shell=True)


@manager.command
def translate():
    """
    Extract translation for all existing locales, creating new mofiles when
    necessary, updating otherwise.  We have to do some tricky stuff to figure
    out which strings are marked for translation in the domains and
    questionnaires.
    """
    locales = set()

    with open('/noi/app/data/deployments.yaml') as deployments_file:
        deployments = yaml.load(deployments_file)

    with open('/noi/app/data/questions.yaml') as questions_file:
        questionnaires = yaml.load(questions_file)

    with codecs.open('/noi/app/templates/translate.tmp.html', 'w', 'utf-8') as totranslate:
        for deployment in deployments.values():
            for domain in deployment.get('domains', []):
                totranslate.write(gettext_for(domain))
            #if 'about' in deployment:
            #    totranslate.write(gettext_for(deployment['about']))
            if 'locale' in deployment:
                locales.add(deployment['locale'])

        for questionnaire in questionnaires:
            totranslate.write(gettext_for(questionnaire['description']))
            totranslate.write(gettext_for(questionnaire['name']))
            if 'topics' in questionnaire:
                for topic in questionnaire['topics']:
                    totranslate.write(gettext_for(topic['topic']))
                    totranslate.write(gettext_for(topic['description']))
                    for question in topic['questions']:
                        totranslate.write(gettext_for(question['question']))

        for level in LEVELS.values():
            totranslate.write(gettext_for(level['label']))

        for org_type in ORG_TYPES.values():
            totranslate.write(gettext_for(org_type))

    # Generate basic messages.pot
    subprocess.check_call(
        'pybabel extract -F /noi/app/babel.cfg -k lazy_gettext -o /noi/app/messages.pot /noi/',
        shell=True)

    # Update all potfiles, create those not yet in existence
    for locale in locales:
        try:
            subprocess.check_call('pybabel update -l {locale} -i /noi/app/messages.pot '
                                  '-d /noi/app/translations/'.format(
                                      locale=locale), shell=True)
        except subprocess.CalledProcessError:
            subprocess.check_call('pybabel init -l {locale} -i /noi/app/messages.pot '
                                  '-d /noi/app/translations/'.format(
                                      locale=locale), shell=True)
        subprocess.check_call('pybabel compile -f -l {locale} -d /noi/app/translations/'.format(
            locale=locale), shell=True)

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
        user = User(**row)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            app.logger.warn('Could not add user with email "%s", as they are '
                            'already in the database.', row['email'])


@manager.command
def setup_db_master():
    '''
    Set up connection to db master using BDR, no-op if MASTER_DATABASE_HOST
    isn't set.
    '''
    if app.config.get('BDR_DB_HOST'):
        try:
            db.session.execute('CREATE EXTENSION IF NOT EXISTS btree_gist;')
            db.session.commit()
            db.session.execute('CREATE EXTENSION IF NOT EXISTS bdr;')
            db.session.commit()
            db.session.execute('''SELECT bdr.bdr_group_join(
                  local_node_name := 'node_{deployment}',
                  node_external_dsn := 'host={db_public_host} port={db_public_port} dbname={db_public_dbname} user={db_public_user} password={db_public_password}',
                  join_using_dsn := 'host={bdr_db_host} port={bdr_db_port} dbname={bdr_db_dbname} user={bdr_db_user} password={bdr_db_password}'
            );
                '''.format(**{'deployment': app.config.get('NOI_DEPLOY', '_default'),
                              'db_public_host': app.config['DB_PUBLIC_HOST'],
                              'db_public_port': app.config['SQLALCHEMY_DATABASE_PORT'],
                              'db_public_dbname': app.config['SQLALCHEMY_DATABASE_DBNAME'],
                              'db_public_user': app.config['SQLALCHEMY_DATABASE_USER'],
                              'db_public_password': app.config['SQLALCHEMY_DATABASE_PASSWORD'],
                              'bdr_db_host': app.config['BDR_DB_HOST'],
                              'bdr_db_port': app.config['BDR_DB_PORT'],
                              'bdr_db_dbname': app.config['BDR_DB_DBNAME'],
                              'bdr_db_user': app.config['BDR_DB_USER'],
                              'bdr_db_password': app.config['BDR_DB_PASSWORD']}))
            db.session.commit()
            app.logger.debug('waiting for bdr')
            #import time
            #time.sleep(15)
            db.engine.execute('SELECT bdr.bdr_node_join_wait_for_ready();')
            db.session.commit()
        except OperationalError:
            app.logger.debug('Already joined BDR group, skipping')



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
        user = User.query_in_deployment().filter_by(email=row['email']).one()
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
