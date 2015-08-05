'''
NoI Models

Creates the app
'''

from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin

from sqlalchemy import types, orm, Column, Table, ForeignKey

import datetime

db = SQLAlchemy()  #pylint: disable=invalid-name


roles_users = Table('roles_users',  #pylint: disable=invalid-name
                    Column('users_id', types.Integer(), ForeignKey('users.id')),
                    Column('roles_id', types.Integer(), ForeignKey('roles.id')))


class User(db.Model, UserMixin): #pylint: disable=no-init,too-few-public-methods
    '''
    User
    '''
    __tablename__ = 'users'

    id = Column(types.Integer, primary_key=True)  #pylint: disable=invalid-name

    first_name = Column(types.Text, nullable=False)
    last_name = Column(types.Text, nullable=False)

    email = Column(types.Text, unique=True, nullable=False)
    password = Column(types.Text, nullable=False)
    active = Column(types.Boolean, nullable=False)

    last_login_at = Column(types.DateTime())
    current_login_at = Column(types.DateTime())
    last_login_ip = Column(types.Text)
    current_login_ip = Column(types.Text)
    login_count = Column(types.Integer)

    country = Column(types.Text)
    country_code = Column(types.Text)
    city = Column(types.Text)

    latlng = Column(types.Text)

    org = Column(types.Text)
    org_type = Column(types.Text)

    #picture text,
    title = Column(types.Text)

    domain_expertise = Column(types.Text)

    projects = Column(types.Text)

    created_at = Column(types.DateTime(), default=datetime.datetime.now)
    updated_at = Column(types.DateTime(), default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)

    # skills json,
    skills = orm.relationship('Skill', secondary='user_skills',
                              backref=orm.backref('users', lazy='dynamic'))

    # langs json,
    # domains json,

    roles = orm.relationship('Role', secondary=roles_users,
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
