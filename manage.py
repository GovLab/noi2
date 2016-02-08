'''
NoI manage.py

Scripts to run the server and perform maintenance operations
'''

from app import (mail, models, sass, email_errors, LEVELS, ORG_TYPES, stats,
                 questionnaires, blog_posts, linkedin)
from app.factory import create_app
from app.models import db, User
from app.utils import csv_reader
from app.tests.factories import UserFactory
from app.noi1 import Noi1Command

from flask_alchemydumps import AlchemyDumps, AlchemyDumpsCommand
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_mail import Message
from flask_security.recoverable import send_reset_password_instructions
from flask.ext.script.commands import InvalidCommand

from random import choice
from sqlalchemy.exc import IntegrityError

import codecs
import sys
import os
import string
import subprocess
import pprint
import yaml

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

app = create_app() #pylint: disable=invalid-name
migrate = Migrate(app, db) #pylint: disable=invalid-name

manager = Manager(app) #pylint: disable=invalid-name

manager.add_command('noi1', Noi1Command)
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
def getstats():
    """
    Generate statistics about the current deployment.
    """

    import json
    print json.dumps(stats.generate(), sort_keys=True, indent=2)


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
def send_test_email(recipient):
    """
    Send a test email to the given recipient.
    """

    msg = Message(
        'Test Email',
        sender=app.config['SECURITY_EMAIL_SENDER'],
        recipients=[recipient]
    )
    msg.body = "Looks like sending email works!"
    mail = app.extensions.get('mail')
    mail.send(msg)


@manager.command
def test_email_error_reporting():
    """
    Test email error reporting by logging an exception.
    """

    try:
        1/0
    except:
        app.logger.exception("This is a test of application error reporting.")

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
def wait_for_db():
    """
    Wait for the database to be ready.
    """

    from app.tests.test_models import wait_until_db_is_ready

    print "Waiting for database to be ready..."
    wait_until_db_is_ready()
    print "Database is ready!"

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
@manager.option('-c', '--count', dest='count', default=100)
def populate_db(count=50):
    """
    Populate DB with random data.
    """
    UserFactory.create_batch(int(count))
    db.session.commit()
    return 0

@manager.command
def show_db_create_table_sql():
    from app.tests.test_models import get_postgres_create_table_sql

    print get_postgres_create_table_sql()

@manager.command
def refresh_linkedin_info(email):
    """
    Refresh and display LinkedIn information for a user.
    """

    user = User.query_in_deployment().filter_by(email=email).one()
    if linkedin.retrieve_access_token(user) is None:
        raise InvalidCommand(
            'The user must first (re)connect to LinkedIn on the website.'
        )
    linkedin.update_user_info(user)
    pprint.pprint(user.linkedin.user_info)

@manager.command
def show_blog_posts():
    """
    Show recent blog posts from BLOG_POSTS_RSS_URL.
    """

    summ = blog_posts.get_and_summarize(app.config['BLOG_POSTS_RSS_URL'])
    pprint.pprint(summ)

@manager.command
def build_sass():
    """
    Build SASS files.
    """

    print "Building SASS files..."
    sass.build_files()
    print "Done. Built SASS files are in app/%s." % sass.CSS_DIR
    return 0

@manager.command
@manager.option('-f', '--from', dest='from_yaml')
@manager.option('-t', '--to', dest='to_yaml')
def generate_question_id_migration(from_yaml, to_yaml):
    """
    Generate an Alembic migration script for YAML question id changes.
    """

    from_yaml = os.path.normpath(os.path.join(ROOT_DIR, from_yaml))
    to_yaml = os.path.normpath(os.path.join(ROOT_DIR, to_yaml))
    from_q = questionnaires.Questionnaires(yaml.load(open(from_yaml)))
    to_q = questionnaires.Questionnaires(yaml.load(open(to_yaml)))
    print from_q.generate_question_id_migration_script(to_q)


if __name__ == '__main__':
    if os.path.exists('../symlink-hooks.sh'):
        subprocess.call('../symlink-hooks.sh', shell=True)
    try:
        manager.run()
    except InvalidCommand as err:
        sys.stderr.write(str(err) + '\n')
        sys.exit(1)
