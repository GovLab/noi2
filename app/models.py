'''
NoI Models

Creates the app
'''

from app import ORG_TYPES

from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from flask_babel import lazy_gettext

from sqlalchemy import orm, types, Column, ForeignKey
from sqlalchemy_utils import EmailType, CountryType

import datetime

db = SQLAlchemy()  #pylint: disable=invalid-name


class User(db.Model, UserMixin): #pylint: disable=no-init,too-few-public-methods
    '''
    User
    '''
    __tablename__ = 'users'

    id = Column(types.Integer, primary_key=True)  #pylint: disable=invalid-name

    first_name = Column(types.String, info={
        'label': lazy_gettext('First Name'),
    })
    last_name = Column(types.String, info={
        'label': lazy_gettext('Last Name'),
    })

    email = Column(EmailType, unique=True, nullable=False, info={
        'label': lazy_gettext('Email'),
    })
    password = Column(types.String, nullable=False, info={
        'label': lazy_gettext('Password'),
    })
    active = Column(types.Boolean, nullable=False)

    last_login_at = Column(types.DateTime())
    current_login_at = Column(types.DateTime())
    last_login_ip = Column(types.Text)
    current_login_ip = Column(types.Text)
    login_count = Column(types.Integer)

    position = Column(types.String, info={
        'label': lazy_gettext('Position'),
    })
    organization = Column(types.String, info={
        'label': lazy_gettext('Organization'),
    })
    organization_type = Column(types.String, info={
        'label': lazy_gettext('Type of Organization'),
        'placeholder': lazy_gettext('The type of organization you work for'),
        'choices': [(k, v) for k, v in ORG_TYPES.iteritems()]
    })
    country = Column(CountryType, info={
        'label': lazy_gettext('Country'),
    })

    country_code = Column(types.String)
    city = Column(types.String)

    latlng = Column(types.String)

    #domain_expertise = Column(types.String)

    projects = Column(types.Text)

    created_at = Column(types.DateTime(), default=datetime.datetime.now)
    updated_at = Column(types.DateTime(), default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)

    # skills json,
    skills = orm.relationship('Skill', secondary='user_skills',
                              backref=orm.backref('users', lazy='dynamic'))

    # langs json,
    # domains json,

    roles = orm.relationship('Role', secondary='role_users',
                             backref=orm.backref('users', lazy='dynamic'))

    #def check_password(self, password):
    #    correct = _security.check_password_hash(self.pw_method_salt,
    #                                            self.password,
    #                                            password)


class Role(db.Model, RoleMixin): #pylint: disable=no-init,too-few-public-methods
    '''
    User role for permissioning
    '''
    __tablename__ = 'roles'

    id = Column(types.Integer, primary_key=True)  #pylint: disable=invalid-name
    name = Column(types.Text, unique=True)
    description = Column(types.Text)



class Skill(db.Model): #pylint: disable=no-init,too-few-public-methods
    '''
    Skills that we match upon
    '''
    __tablename__ = 'skills'

    id = Column(types.Integer, primary_key=True)  #pylint: disable=invalid-name

    name = Column(types.Text)
    created_at = Column(types.DateTime(), default=datetime.datetime.now)
    updated_at = Column(types.DateTime(), default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)


class RoleUser(db.Model): #pylint: disable=no-init,too-few-public-methods
    '''
    Join table between a user and her roles.
    '''
    __tablename__ = 'role_users'

    id = Column(types.Integer, primary_key=True)  #pylint: disable=invalid-name

    users_id = Column(types.Integer(), ForeignKey('users.id'), nullable=False)
    roles_id = Column(types.Integer(), ForeignKey('roles.id'), nullable=False)


class UserSkill(db.Model): #pylint: disable=no-init,too-few-public-methods
    '''
    Join table between users and their skills, which includes their level of
    knowledge for that skill (level).
    '''
    __tablename__ = 'user_skills'

    id = Column(types.Integer, primary_key=True)  #pylint: disable=invalid-name

    created_at = Column(types.DateTime(), default=datetime.datetime.now)
    updated_at = Column(types.DateTime(), default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)

    level = Column(types.Integer, nullable=False)

    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False)
    skill_id = Column(types.Integer, ForeignKey('skills.id'), nullable=False)
