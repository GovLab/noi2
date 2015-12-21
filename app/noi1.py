import os
import sys
import json
import requests
import mimetypes
import datetime
import functools
from warnings import warn
from boto.s3.connection import S3Connection
from slugify import slugify
from sqlalchemy_utils import Country
from flask_script import Manager
from flask.ext.script.commands import InvalidCommand
from flask import current_app

import app
from app.factory import create_app
from app.models import (db, User, UserExpertiseDomain, UserLanguage,
                        UserSkill, UserJoinedEvent)

DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'noi1')

datapath = lambda *x: os.path.join(DATA_DIR, *x)

USERS_FILE = datapath('users.json')
PICTURES_DIR = datapath('pictures')
PICTURE_EXTS = ['.jpg', '.png']
MIN_SKILLS = 3
FAKE_DEV_PASSWORD = 'foobar'

class Noi1Manager(Manager):
    @staticmethod
    def __setup_globals():
        global users, users_with_skills, users_with_email

        if not os.path.exists(DATA_DIR):
            os.mkdir(DATA_DIR)

        if not os.path.exists(USERS_FILE):
            raise InvalidCommand(
                "Please export all NoI 1.0 users to %s." % USERS_FILE
            )

        users = json.load(open(USERS_FILE, 'r'))
        users_with_skills = [user for user in users if has_skills(user)]
        users_with_email = [user for user in users if user['email']]

    def command(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.__setup_globals()
            func(*args, **kwargs)

        return super(Noi1Manager, self).command(wrapper)

Noi1Command = manager = Noi1Manager(usage='Migrate NoI 1.0 users')

def has_skills(user, min_skills=MIN_SKILLS):
    return user['skills'] and len(user['skills'].keys()) >= min_skills

def set_user_picture(user, filename):
    # This is largely copy/pasted from views.py, which we're not using
    # directly because it's super complicated ugh.

    conn = S3Connection(current_app.config['S3_ACCESS_KEY_ID'],
                        current_app.config['S3_SECRET_ACCESS_KEY'])
    bucket = conn.get_bucket(current_app.config['S3_BUCKET_NAME'])
    bucket.make_public(recursive=False)

    mimetype = mimetypes.guess_type(filename)[0]

    k = bucket.new_key(user.picture_path)
    k.set_metadata('Content-Type', mimetype)
    k.set_contents_from_file(open(filename, 'r'))
    k.make_public()

    user.has_picture = True

def get_imported_users(users):
    for json_user in users:
        yield User.query_in_deployment().\
          filter(User.email==json_user['email']).\
          one(), json_user

def add_user_to_db(user):
    timestamp = datetime.datetime.strptime(
        user['timestamp'].split('.')[0],
        "%Y-%m-%dT%H:%M:%S"
    )
    u = User(
        first_name=user['first_name'],
        last_name=user['last_name'],
        email=user['email'],
        organization=user['org'],
        projects=user['projects'],
        position=user['title'],
        city=user['city'],
        created_at=timestamp,
        updated_at=timestamp,
        # TODO: Change this for production!
        password=FAKE_DEV_PASSWORD,
        active=True
    )
    if user['org_type']:
        if user['org_type'] in app.ORG_TYPES:
            u.organization_type = user['org_type']
        else:
            warn("invalid org_type: %s" % user['org_type'])
    if user['domains']:
        for domain in user['domains']:
            if domain in current_app.config['DOMAINS']:
                u.expertise_domains.append(UserExpertiseDomain(
                    name=domain
                ))
            else:
                warn("invalid domain: %s" % domain)
    if user['country_code']:
        try:
            u.country = Country(user['country_code'])
        except ValueError, e:
            warn(str(e))
    if user['langs']:
        for lang in user['langs']:
            locs = [loc for loc in app.LOCALES
                    if loc.english_name == lang]
            if len(locs) == 1:
                u.languages.append(UserLanguage(
                    locale=locs[0]
                ))
            else:
                warn("unknown language: %s" % lang)
    if user['skills']:
        for skill_id, score in user['skills'].items():
            score = int(score)
            if score in app.LEVELS_BY_SCORE:
                skill_id = skill_id.replace('/', '-')
                if skill_id in app.QUESTIONS_BY_ID:
                    u.skills.append(UserSkill(
                        level=score,
                        name=skill_id
                    ))
                else:
                    warn("unknown question id: %s" % skill_id)
            else:
                warn("invalid score: %s" % score)
    db.session.add(u)

@manager.command
def import_pictures():
    '''
    Import pictures for imported users.
    '''

    for user, json_user in get_imported_users(users_with_email):
        if not user.has_picture:
            cached_picture = find_cached_picture(json_user)
            if cached_picture:
                print "Setting picture for %s." % user.email
                set_user_picture(user, cached_picture)
                db.session.commit()

@manager.command
def fully_register_users():
    '''
    Set imported users as being fully registered.
    '''

    for user, _ in get_imported_users(users_with_email):
        if not user.has_fully_registered:
            if len(user.skills) >= app.MIN_QUESTIONS_TO_JOIN:
                print "Fully registering %s." % user.email
                event = UserJoinedEvent.from_user(user)
                event.created_at = event.updated_at = user.created_at
                db.session.add(event)
    db.session.commit()

@manager.command
def import_users():
    '''
    Import users into the database.
    '''

    for user in users_with_email:
        users = User.query_in_deployment().filter(User.email==user['email'])
        if users.all():
            print "User with email %(email)s exists, skipping." % user
        else:
            print "Adding user %(email)s." % user
            add_user_to_db(user)
    db.session.commit()

@manager.command
def validate():
    '''
    Validate user fields and report any problems.
    '''

    print "Validating users..."
    user_emails = {}
    for user in users_with_email:
        if user['email'] in user_emails:
            warn('multiple users exist with email %(email)s' % user)
        user_emails[user['email']] = True
        add_user_to_db(user)
    db.session.rollback()
    print "Validation complete."

def get_cached_picture_base_path(user):
    picture_path = slugify('%s %s %s' % (user['first_name'],
                                         user['last_name'],
                                         user['userid']))
    return os.path.join(PICTURES_DIR, picture_path)

def find_cached_picture(user):
    base = get_cached_picture_base_path(user)
    filenames = [base + ext for ext in PICTURE_EXTS]
    for filename in filenames:
        if os.path.exists(filename):
            return filename
    return None

@manager.command
def cache_pictures():
    '''
    Cache user pictures to filesystem.
    '''

    if not os.path.exists(PICTURES_DIR):
        os.mkdir(PICTURES_DIR)

    for user in users_with_email:
        if not user['picture']: continue
        if find_cached_picture(user): continue

        print "caching picture for %s" % user['userid']

        req = requests.get(user['picture'])
        if req.status_code == 200:
            picture_path = get_cached_picture_base_path(user)
            ext = mimetypes.guess_extension(req.headers['content-type'])

            if ext == '.jpe':
                # Weird.
                ext = '.jpg'

            if ext not in PICTURE_EXTS:
                print "  unknown extension for picture: %s" % ext
                continue

            content = req.content
            f = open(picture_path + ext, 'w')
            f.write(content)
            f.close()
        else:
            print "  got HTTP %d" % req.status_code

@manager.command
def stats():
    '''
    Display statistics about users.
    '''

    print "by 'skilled users' we mean users w/ at least %d skill(s)." % (
        MIN_SKILLS
    )

    print "total users: %s" % len(users)

    print "total skilled users: %s" % len(users_with_skills)

    print "skilled users w/ email: %s" % (
        len([user for user in users_with_skills if user['email']])
    )

    print "skilled users w/o email: %s" % (
        len([user for user in users_with_skills if not user['email']])
    )

    print "unskilled users w/ email: %s" % (
        len([user for user in users
             if user['email'] and user not in users_with_skills])
    )

    print "users w/o email, but with org names: %s" % (
        len([user for user in users
            if not user['email'] and user['org']])
    )

    login_type_counts = {}

    for user in users_with_skills:
        login_type = user['userid'].split(':')[0]
        if login_type not in login_type_counts:
            login_type_counts[login_type] = 0
        login_type_counts[login_type] += 1

    print "login types for skilled users:"

    print json.dumps(login_type_counts, indent=4)
