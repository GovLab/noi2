'''
NoI Models

Creates the app
'''

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import UserMixin #, RoleMixin

import datetime

db = SQLAlchemy()


class User(db.Model, UserMixin): #pylint: disable=no-init,too-few-public-methods
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)

    email = db.Column(db.Text, unique=True)

    country = db.Column(db.Text)
    country_code = db.Column(db.Text)
    city = db.Column(db.Text)

    latlng = db.Column(db.Text)

    org = db.Column(db.Text)
    org_type = db.Column(db.Text)

    #picture text,
    title = db.Column(db.Text)

    domain_expertise = db.Column(db.Text)

    projects = db.Column(db.Text)

    created_at = db.Column(db.DateTime(), default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime(), default=datetime.datetime.now,
                           onupdate=datetime.datetime.now)

    # skills json,
    skills = db.relationship('Skill', secondary='user_skills',
                             backref=db.backref('users', lazy='dynamic'))

    # langs json,
    # domains json,


class Skill(db.Model): #pylint: disable=no-init,too-few-public-methods
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.Text)
    created_at = db.Column(db.DateTime(), default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime(), default=datetime.datetime.now,
                           onupdate=datetime.datetime.now)


class UserSkill(db.Model): #pylint: disable=no-init,too-few-public-methods
    __tablename__ = 'user_skills'

    id = db.Column(db.Integer, primary_key=True)

    created_at = db.Column(db.DateTime(), default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime(), default=datetime.datetime.now,
                           onupdate=datetime.datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'))
