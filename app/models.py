'''
NoI Models

SQLAlchemy models for the app
'''

from app import ORG_TYPES, VALID_SKILL_LEVELS, QUESTIONS_BY_ID, LEVELS

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from flask_babel import lazy_gettext

from sqlalchemy import (orm, types, Column, ForeignKey, UniqueConstraint, func)
from sqlalchemy.orm import aliased
from sqlalchemy_utils import EmailType, CountryType, LocaleType
from sqlalchemy.ext.hybrid import hybrid_property

import base64
import datetime
import os

db = SQLAlchemy()  #pylint: disable=invalid-name


class User(db.Model, UserMixin): #pylint: disable=no-init,too-few-public-methods
    '''
    User
    '''
    __tablename__ = 'users'

    id = Column(types.Integer, autoincrement=True, primary_key=True)  #pylint: disable=invalid-name

    picture_id = Column(types.String,
                        default=lambda: base64.urlsafe_b64encode(os.urandom(20))[0:-2])

    has_picture = Column(types.Boolean, default=False)
    deployment = Column(types.String, nullable=False,
                        default=lambda: current_app.config['NOI_DEPLOY'])

    first_name = Column(types.String, info={
        'label': lazy_gettext('First Name'),
    })
    last_name = Column(types.String, info={
        'label': lazy_gettext('Last Name'),
    })

    email = Column(EmailType, nullable=False, info={
        'label': lazy_gettext('Email'),
    })

    password = Column(types.String, nullable=False, info={
        'label': lazy_gettext('Password'),
    })
    active = Column(types.Boolean, nullable=False)

    last_login_at = Column(types.DateTime())
    current_login_at = Column(types.DateTime())
    confirmed_at = Column(types.DateTime())
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
        'description': lazy_gettext('The type of organization you work for'),
        'choices': [(k, v) for k, v in ORG_TYPES.iteritems()]
    })
    country = Column(CountryType, info={
        'label': lazy_gettext('Country'),
    })

    city = Column(types.String, info={
        'label': lazy_gettext('City')
    })

    latlng = Column(types.String, info={
        'label': lazy_gettext('Location'),
        'description': lazy_gettext('Enter your location')
    })

    projects = Column(types.Text, info={
        'label': lazy_gettext('Projects'),
        'description': lazy_gettext(
            'Add name and url or short description of any current work projects.')
    })

    created_at = Column(types.DateTime(), default=datetime.datetime.now)
    updated_at = Column(types.DateTime(), default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)

    @classmethod
    def query_in_deployment(cls):
        '''
        Query for users within this deployment
        '''
        return cls.query.filter(cls.deployment.in_(current_app.config['SEARCH_DEPLOYMENTS']))

    @property
    def display_in_search(self):
        '''
        Determine whether user has filled out bare minimum to display in search
        results.
        '''
        return self.first_name is not None and self.last_name is not None

    @property
    def picture_path(self):
        '''
        Path where picture would be found (hosted on S3).
        '''
        return "{}/static/pictures/{}/{}".format(
            current_app.config['NOI_DEPLOY'],
            self.id, self.picture_id)

    @property
    def picture_url(self):
        '''
        Full path to picture.
        '''
        return 'https://s3.amazonaws.com/{bucket}/{path}'.format(
            bucket=current_app.config['S3_BUCKET_NAME'],
            path=self.picture_path
        )

    @property
    def helpful_users(self, limit=10):
        '''
        Returns a list of users with matching positive skills, ordered by the
        most helpful (highest score) descending.
        '''
        learn_level = LEVELS['LEVEL_I_WANT_TO_LEARN']['score']
        skills_needing_help = [s.name for s in self.skills if s.level == learn_level]
        user_id_scores = dict(db.session.query(UserSkill.user_id, func.sum(UserSkill.level)).\
                              filter(UserSkill.name.in_(skills_needing_help)).\
                              filter(UserSkill.level > learn_level).\
                              group_by(UserSkill.user_id).\
                              limit(limit).all())
        users = db.session.query(User).\
                filter(User.id.in_(user_id_scores.keys())).all()
        for user in users:
            user.score = user_id_scores[user.id]
        return sorted(users, key=lambda x: x.score, reverse=True)

    @property
    def nearest_neighbors(self, limit=10):
        '''
        Returns a list of users with the closest matching skills.  If they
        haven't answered the equivalent skill question, we consider that a very
        big difference (10).
        '''
        # TODO optimize, this would get unwieldy with a few thousand answers
        # TODO use outerjoin, right now the coalesce does nothing

        #skills = [s.name for s in self.skills]

        me = aliased(UserSkill)
        user_id_scores = dict(db.session.query(
            UserSkill.user_id, func.sum(func.coalesce(UserSkill.level, 10) - me.level)).\
            filter(UserSkill.user_id != self.id).\
            filter(me.user_id == self.id).\
            filter(UserSkill.name.in_([me.name, None])).\
            group_by(UserSkill.user_id).\
            limit(limit).all())

        users = db.session.query(User).\
                filter(User.id.in_(user_id_scores.keys())).all()
        for user in users:
            user.score = user_id_scores[user.id]
        return sorted(users, key=lambda x: x.score)


    @property
    def skill_levels(self):
        '''
        Dictionary of this user's entered skills, keyed by the id of the skill.
        '''
        return dict([(skill.name, skill.level) for skill in self.skills])

    def set_skill(self, skill_name, skill_level):
        '''
        Set the level of a single skill by name.
        '''
        if skill_name not in QUESTIONS_BY_ID:
            return
        try:
            if int(skill_level) not in VALID_SKILL_LEVELS:
                return
        except ValueError:
            return
        for skill in self.skills:
            if skill_name == skill.name:
                skill.level = skill_level
                db.session.add(skill)
                return
        db.session.add(UserSkill(user_id=self.id,
                                 name=skill_name,
                                 level=skill_level))

    roles = orm.relationship('Role', secondary='role_users',
                             backref=orm.backref('users', lazy='dynamic'))

    expertise_domains = orm.relationship('UserExpertiseDomain', cascade='all,delete-orphan')
    languages = orm.relationship('UserLanguage', cascade='all,delete-orphan')
    skills = orm.relationship('UserSkill', cascade='all,delete-orphan')

    @hybrid_property
    def expertise_domain_names(self):
        '''
        Convenient list of expertise domains by name.
        '''
        return [ed.name for ed in self.expertise_domains]

    @expertise_domain_names.setter
    def _expertise_domains_setter(self, values):
        '''
        Update expertise domains in bulk.  Values are array of names.
        '''
        # Only add new expertise
        for val in values:
            if val not in self.expertise_domain_names:
                db.session.add(UserExpertiseDomain(name=val,
                                                   user_id=self.id))
        # delete expertise no longer found
        expertise_to_remove = []
        for exp in self.expertise_domains:
            if exp.name not in values:
                expertise_to_remove.append(exp)

        for exp in expertise_to_remove:
            self.expertise_domains.remove(exp)


    @hybrid_property
    def locales(self):
        '''
        Convenient list of locales for this user.
        '''
        return [l.locale for l in self.languages]

    @locales.setter
    def _languages_setter(self, values):
        '''
        Update locales for this user in bulk.  Values are an array of language
        codes.
        '''
        locale_codes = [l.language for l in self.locales]
        # only add new languages
        for val in values:
            if val not in locale_codes:
                db.session.add(UserLanguage(locale=val, user_id=self.id))

        # delete languages no longer found
        languages_to_remove = []
        for lan in self.languages:
            if lan.locale.language not in values:
                languages_to_remove.append(lan)

        for lan in languages_to_remove:
            self.languages.remove(lan)

    __table_args__ = (UniqueConstraint('deployment', 'email'),)


class UserExpertiseDomain(db.Model):  #pylint: disable=no-init,too-few-public-methods
    '''
    Expertise domain of a single user.  List is read from YAML.
    '''
    __tablename__ = 'user_expertise_domains'

    id = Column(types.Integer, autoincrement=True, primary_key=True)  #pylint: disable=invalid-name
    name = Column(types.String, nullable=False)

    user_id = Column(types.Integer(), ForeignKey('users.id'), nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'name'),)

class UserLanguage(db.Model):  #pylint: disable=no-init,too-few-public-methods
    '''
    Language of a single user.
    '''
    __tablename__ = 'user_languages'

    id = Column(types.Integer, autoincrement=True, primary_key=True)  #pylint: disable=invalid-name
    locale = Column(LocaleType, nullable=False)

    user_id = Column(types.Integer(), ForeignKey('users.id'), nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'locale'),)


class Role(db.Model, RoleMixin): #pylint: disable=no-init,too-few-public-methods
    '''
    User role for permissioning
    '''
    __tablename__ = 'roles'

    id = Column(types.Integer, autoincrement=True, primary_key=True)  #pylint: disable=invalid-name
    name = Column(types.Text, unique=True)
    description = Column(types.Text)


class RoleUser(db.Model): #pylint: disable=no-init,too-few-public-methods
    '''
    Join table between a user and her roles.
    '''
    __tablename__ = 'role_users'

    id = Column(types.Integer, autoincrement=True, primary_key=True)  #pylint: disable=invalid-name

    user_id = Column(types.Integer(), ForeignKey('users.id'), nullable=False)
    role_id = Column(types.Integer(), ForeignKey('roles.id'), nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'role_id'),)


class UserSkill(db.Model): #pylint: disable=no-init,too-few-public-methods
    '''
    Join table between users and their skills, which includes their level of
    knowledge for that skill (level).
    '''
    __tablename__ = 'user_skills'

    id = Column(types.Integer, autoincrement=True, primary_key=True)  #pylint: disable=invalid-name

    created_at = Column(types.DateTime(), default=datetime.datetime.now)
    updated_at = Column(types.DateTime(), default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)

    level = Column(types.Integer, nullable=False)
    name = Column(types.String, nullable=False)

    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'name'),)
