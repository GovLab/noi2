'''
NoI Models

SQLAlchemy models for the app
'''

from app import (ORG_TYPES, VALID_SKILL_LEVELS, LEVELS, QUESTIONNAIRES,
                 QUESTIONNAIRES_BY_ID, QUESTIONS_BY_ID)
from app.utils import UserSkillMatch

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from flask_babel import lazy_gettext

from sqlalchemy import (orm, types, Column, ForeignKey, UniqueConstraint, func,
                        desc, cast, String)
from sqlalchemy.orm import aliased
from sqlalchemy_utils import EmailType, CountryType, LocaleType
from sqlalchemy.ext.hybrid import hybrid_property
from boto.s3.connection import S3Connection

import base64
import datetime
import os

db = SQLAlchemy()  #pylint: disable=invalid-name


def skills_to_percentages(s):
    '''
    >>> skills_to_percentages(dict(learn=5, explain=5, connect=0, do=0))
    {'do': 0, 'explain': 50, 'connect': 0, 'learn': 50}
    '''

    total = s['learn'] + s['explain'] + s['connect'] + s['do']
    percentages = {}
    for skill_level in ['learn', 'explain', 'connect', 'do']:
        percentage = 0.0
        if total > 0:
            percentage = float(s[skill_level]) / total
        percentages[skill_level] = int(percentage * 100)
    return percentages


def scores_to_skills(score_dict):
    '''
    >>> scores_to_skills({-1: 5})
    {'do': 0, 'explain': 0, 'connect': 0, 'learn': 5}
    '''

    return {
        'learn': score_dict.get(
            LEVELS['LEVEL_I_WANT_TO_LEARN']['score'],
            0
        ),
        'explain': score_dict.get(
            LEVELS['LEVEL_I_CAN_EXPLAIN']['score'],
            0
        ),
        'connect': score_dict.get(
            LEVELS['LEVEL_I_CAN_REFER']['score'],
            0
        ),
        'do': score_dict.get(
            LEVELS['LEVEL_I_CAN_DO_IT']['score'],
            0
        )
    }

class DeploymentMixin(object):
    '''
    Mixin class for any model that is accessible on a per-deployment
    basis.
    '''

    deployment = Column(types.String, nullable=False,
                        default=lambda: current_app.config['NOI_DEPLOY'])

    @classmethod
    def query_in_deployment(cls):
        '''
        Query for instances of the model within this deployment.
        '''

        deployments = current_app.config['SEARCH_DEPLOYMENTS']
        return cls.query.filter(cls.deployment.in_(deployments))

class User(db.Model, UserMixin, DeploymentMixin): #pylint: disable=no-init,too-few-public-methods
    '''
    User
    '''
    __tablename__ = 'users'

    id = Column(types.Integer, autoincrement=True, primary_key=True)  #pylint: disable=invalid-name

    picture_id = Column(types.String,
                        default=lambda: base64.urlsafe_b64encode(os.urandom(20))[0:-2])

    has_picture = Column(types.Boolean, default=False)

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

    tutorial_step = Column(types.Integer())

    created_at = Column(types.DateTime(), default=datetime.datetime.now)
    updated_at = Column(types.DateTime(), default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)

    def is_admin(self):
        return self.email in current_app.config.get('ADMIN_UI_USERS', [])

    @property
    def full_name(self):
        return u"%s %s" % (self.first_name, self.last_name)

    @property
    def full_location(self):
        loc = []
        if self.city:
            loc.append(self.city)
        if self.country and self.country.code != 'ZZ':
            loc.append(self.country.name)
        return ", ".join(loc)

    @property
    def display_in_search(self):
        '''
        Determine whether user has filled out bare minimum to display in search
        results.

        Specifically, we want to make sure that the first and last name
        are both non-NULL and non-blank.
        '''
        return bool(self.first_name and self.last_name)

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

    def upload_picture(self, fileobj, mimetype):
        '''
        Upload the given file object with the given mime type to S3 and
        mark the user as having a picture.
        '''

        conn = S3Connection(current_app.config['S3_ACCESS_KEY_ID'],
                            current_app.config['S3_SECRET_ACCESS_KEY'])
        bucket = conn.get_bucket(current_app.config['S3_BUCKET_NAME'])
        bucket.make_public(recursive=False)

        k = bucket.new_key(self.picture_path)
        k.set_metadata('Content-Type', mimetype)
        k.set_contents_from_file(fileobj)
        k.make_public()

        self.has_picture = True

    @property
    def helpful_users(self, limit=10):
        '''
        Returns a list of (user, score) tuples with matching positive skills,
        ordered by the most helpful (highest score) descending.
        '''
        my_skills = aliased(UserSkill, name='my_skills', adapt_on_names=True)
        their_skills = aliased(UserSkill, name='their_skills', adapt_on_names=True)

        return User.query_in_deployment().\
                add_column(func.sum(their_skills.level - my_skills.level)).\
                filter(their_skills.user_id != my_skills.user_id).\
                filter(User.id == their_skills.user_id).\
                filter(their_skills.name == my_skills.name).\
                filter(my_skills.user_id == self.id).\
                filter(my_skills.level == LEVELS['LEVEL_I_WANT_TO_LEARN']['score']).\
                group_by(User).\
                order_by(desc(func.sum(their_skills.level - my_skills.level))).\
                limit(limit)

    @property
    def nearest_neighbors(self, limit=10):
        '''
        Returns a list of (user, score) tuples with the closest matching
        skills.  If they haven't answered the equivalent skill question, we
        consider that a very big difference (12).

        Order is closest to least close, which is an ascending score.
        '''
        my_skills = aliased(UserSkill, name='my_skills', adapt_on_names=True)
        their_skills = aliased(UserSkill, name='their_skills', adapt_on_names=True)

        # difference we assume for user that has not answered question
        unanswered_difference = (LEVELS['LEVEL_I_CAN_DO_IT']['score'] -
                                 LEVELS['LEVEL_I_WANT_TO_LEARN']['score']) * 2

        return User.query_in_deployment().\
                add_column(((len(self.skills) - func.count(func.distinct(their_skills.id))) *
                            unanswered_difference) + \
                       func.sum(func.abs(their_skills.level - my_skills.level))).\
                filter(their_skills.user_id != my_skills.user_id).\
                filter(User.id == their_skills.user_id).\
                filter(their_skills.name == my_skills.name).\
                filter(my_skills.user_id == self.id).\
                group_by(User).\
                order_by(((len(self.skills) - func.count(func.distinct(their_skills.id)))
                          * unanswered_difference) + \
                     func.sum(func.abs(their_skills.level - my_skills.level))).\
                limit(limit)

    @property
    def has_fully_registered(self):
        '''
        Returns whether the user has fully completed the registration/signup
        flow.
        '''

        return db.session.query(UserJoinedEvent).\
               filter_by(user_id=self.id).\
               first() is not None

    def set_fully_registered(self):
        '''
        Marks the user as having fully completed the registration/signup
        flow, if they haven't already.
        '''

        if self.has_fully_registered:
            return
        db.session.add(UserJoinedEvent.from_user(self))

    def match(self, level, limit=10):
        '''
        Returns a list of UserSkillMatch objects, in descending order of number
        of skills matched for each user.
        '''
        if db.engine.name == 'sqlite':
            agg = func.group_concat
        elif db.engine.name == 'postgresql':
            agg = func.string_agg
        else:
            raise Exception('Unknown aggregation function for DB {}'.format(
                db.engine.name))
        skills_to_learn = [
            s.name for s in
            self.skills if s.level == LEVELS['LEVEL_I_WANT_TO_LEARN']['score']
        ]
        if skills_to_learn:
            matched_users = User.query_in_deployment().\
                            add_column(agg(UserSkill.name, ',')).\
                            add_column(func.count(UserSkill.id)).\
                            filter(UserSkill.name.in_(skills_to_learn)).\
                            filter(User.id == UserSkill.user_id).\
                            filter(UserSkill.level == level).\
                            filter(UserSkill.user_id != self.id).\
                            group_by(User).\
                            order_by(func.count().desc()).\
                            limit(limit)
        else:
            matched_users = []

        for user, question_ids_by_comma, count in matched_users:
            yield UserSkillMatch(user, question_ids_by_comma.split(','))

    def match_against(self, user):
        '''
        Returns a list of three-tuples in the format:

        (<questionnaire id>, <count of matching questions>, <skill dict>, )

        In descending order of <count of matching questions>.

        <skill dict> is keyed by the skill level of the other user, with each
        value being a set of questions they can answer at that level.
        '''
        skills = UserSkill.query.\
                filter(UserSkill.user_id == user.id).\
                filter(UserSkill.name.in_(
                    [s.name for s in
                     self.skills if s.level == LEVELS['LEVEL_I_WANT_TO_LEARN']['score']
                    ])).all()

        resp = {}
        for skill in skills:
            question = QUESTIONS_BY_ID[skill.name]
            questionnaire_id = question['questionnaire']['id']
            if questionnaire_id not in resp:
                resp[questionnaire_id] = dict()

            if skill.level not in resp[questionnaire_id]:
                resp[questionnaire_id][skill.level] = set()
            resp[questionnaire_id][skill.level].add(skill.name)

        resp = [(qname,
                 sum([len(questions) for questions in skill_levels.values()]),
                 skill_levels) for qname, skill_levels in resp.items()]

        return sorted(resp, lambda a, b: a[1] - b[1], reverse=True)

    def match_against_with_progress(self, user):
        '''
        Like match_against(), but also includes information about
        areas of expertise the target user has that we don't match
        on.
        '''

        progress = user.questionnaire_progress
        matches = self.match_against(user)
        match_areas = {}

        for questionnaire_id, _, _ in matches:
            match_areas[questionnaire_id] = True

        for questionnaire_id, progress in progress.items():
            if (questionnaire_id not in match_areas
                and progress['answered'] > 0):
                matches.append((questionnaire_id, 0, {}))

        return matches

    def match_against_with_progress_in_area(self, user, areaid):
        '''
        Return a tuple of (matched_skill_dict, unmatched_skill_dict)
        for the given area.

        matched_skill_dict contains information about skills that
        the target user has which we want to learn, while
        unmatched_skill_dict contains all other skills the target
        user has.

        Each dict is keyed by the skill level of the other user,
        with each value being a set of questions they can answer at that
        level.
        '''

        questionnaire = QUESTIONNAIRES_BY_ID[areaid]
        matches = self.match_against(user)

        matched_skill_dict = {}
        matched_skills = {}

        for questionnaire_id, _, skill_dict in matches:
            if questionnaire_id == areaid:
                matched_skill_dict = skill_dict
                break

        for question_ids in matched_skill_dict.values():
            for question_id in question_ids:
                matched_skills[question_id] = True

        unmatched_skill_dict = {}
        skill_levels = user.skill_levels
        for topic in questionnaire.get('topics', []):
            for question in topic['questions']:
                qid = question['id']
                if (qid in skill_levels and qid not in matched_skills):
                    level = skill_levels[qid]
                    if level not in unmatched_skill_dict:
                        unmatched_skill_dict[level] = []
                    unmatched_skill_dict[level].append(qid)

        return (matched_skill_dict, unmatched_skill_dict)

    @property
    def questionnaire_progress(self):
        '''
        Return a dictionary mapping top-level skill area IDs (e.g.,
        'opendata', 'prizes') to information about how many questions
        the user has answered in that skill area.
        '''

        skill_levels = self.skill_levels
        progress = {}
        for questionnaire in QUESTIONNAIRES:
            topic_progress = {
                'answered': 0,
                'total': 0
            }
            progress[questionnaire['id']] = topic_progress
            for topic in questionnaire.get('topics', []):
                for question in topic['questions']:
                    topic_progress['total'] += 1
                    if question['id'] in skill_levels:
                        topic_progress['answered'] += 1
        return progress

    @property
    def skill_levels(self):
        '''
        Dictionary of this user's entered skills, keyed by the id of the skill.
        '''
        return dict([(skill.name, skill.level) for skill in self.skills])

    @property
    def connections(self):
        '''
        Count the number of distinct email addresses this person has sent or
        received messages from in the deployment.
        '''
        sent = db.session.query(func.count(func.distinct(Email.to_user_id))).\
                filter(Email.to_user_id != self.id).\
                filter(Email.from_user_id == self.id).first()[0]
        received = db.session.query(func.count(func.distinct(Email.from_user_id))).\
                filter(Email.from_user_id != self.id).\
                filter(Email.to_user_id == self.id).first()[0]
        return sent + received

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

    def email_connect(self, users):
        '''
        Indicate that this user has opened an email window with this list of
        users as recipients.
        '''
        event = ConnectionEvent()
        for user in users:
            event.emails.append(Email(from_user_id=self.id, to_user_id=user.id))

        db.session.add(event)
        return event

    roles = orm.relationship('Role', secondary='role_users',
                             backref=orm.backref('users', lazy='dynamic'))

    expertise_domains = orm.relationship('UserExpertiseDomain', cascade='all,delete-orphan', backref='user')
    languages = orm.relationship('UserLanguage', cascade='all,delete-orphan', backref='user')
    skills = orm.relationship('UserSkill', cascade='all,delete-orphan', backref='user')

    @classmethod
    def get_most_complete_profiles(cls, limit=10):
        '''
        Obtain a list of most complete profiles, as (User, score) tuples.
        '''
        return User.query_in_deployment().\
                add_column(func.count(UserSkill.id)).\
                filter(User.id == UserSkill.user_id).\
                group_by(User).\
                order_by(func.count(UserSkill.id).desc()).\
                limit(limit)

    @classmethod
    def get_most_connected_profiles(cls, limit=10):
        '''
        Obtain a list of most connected profiles, as descending (User, score)
        tuples.
        '''
        count_of_unique_emails = func.count(func.distinct(cast(Email.to_user_id, String) + '-' +
                                                          cast(Email.from_user_id, String)))
        return User.query_in_deployment().\
                add_column(count_of_unique_emails).\
                filter((User.id == Email.from_user_id) | (User.id == Email.to_user_id)).\
                group_by(User).\
                order_by(count_of_unique_emails.desc()).\
                limit(limit)

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


    def get_area_scores(self):
        skill_levels = self.skill_levels
        result = {}

        NO_ANSWER = -999

        for questionnaire in QUESTIONNAIRES:
            if not questionnaire['questions']:
                continue
            max_score = NO_ANSWER
            answers_with_score = {}
            for question in questionnaire['questions']:
                if question['id'] in skill_levels:
                    score = skill_levels[question['id']]
                    if score > max_score:
                        max_score = score
                    if score not in answers_with_score:
                        answers_with_score[score] = 0
                    answers_with_score[score] += 1
            reported_max_score = None
            if max_score != NO_ANSWER:
                reported_max_score = max_score
            result[questionnaire['id']] = {
                'skills': scores_to_skills(answers_with_score),
                'max_score': reported_max_score
            }

        return result


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


class Email(db.Model): #pylint: disable=no-init,too-few-public-methods
    '''
    An email sent from one user to another.
    '''
    __tablename__ = 'email'

    id = Column(types.Integer, autoincrement=True, primary_key=True)  #pylint: disable=invalid-name
    created_at = Column(types.DateTime(), default=datetime.datetime.now)
    updated_at = Column(types.DateTime(), default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)

    from_user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False)
    to_user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False)
    from_user = orm.relationship('User', foreign_keys=[from_user_id],
        backref=orm.backref('emails_sent', cascade='all, delete-orphan'))
    to_user = orm.relationship('User', foreign_keys=[to_user_id],
        backref=orm.backref('emails_received', cascade='all, delete-orphan'))

    connection_event_id = Column(types.Integer, ForeignKey('events.id'),
                                 nullable=False)
    connection_event = orm.relationship('ConnectionEvent', backref=orm.backref(
        'emails', lazy='dynamic'))


class Event(db.Model, DeploymentMixin):
    '''
    An event that shows up in the activity feed for a deployment.
    '''

    __tablename__ = 'events'
    id = Column(types.Integer, autoincrement=True, primary_key=True)  #pylint: disable=invalid-name
    created_at = Column(types.DateTime(), default=datetime.datetime.now)
    updated_at = Column(types.DateTime(), default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)
    type = Column(types.String)

    __mapper_args__ = {
        'polymorphic_identity': 'event',
        'polymorphic_on': type
    }


class ConnectionEvent(Event):
    '''
    A user connected to other user(s).
    '''
    __mapper_args__ = {
        'polymorphic_identity': 'connection_event'
    }

    total_connections = Column(types.Integer)

    def set_total_connections(self):
        self.total_connections = ConnectionEvent.connections_in_deployment()

    @classmethod
    def connections_in_deployment(cls):
        '''
        Count total number of distinct connections in deployment.  This must
        be done after committing the emails originally associated with this
        event.
        '''
        return db.session.query(func.count(func.distinct(
            cast(Email.to_user_id, String) + '-' +
            cast(Email.from_user_id, String)))).first()[0]


class UserEvent(Event):
    '''
    An activity feed event whose subject is a particular user.
    '''

    __tablename__ = 'user_events'

    id = Column(types.Integer, ForeignKey('events.id'), primary_key=True)
    user_id = Column(types.Integer, ForeignKey('users.id'))
    user = orm.relationship('User', backref='events')

    __mapper_args__ = {
        'polymorphic_identity': 'user_event'
    }

    @classmethod
    def from_user(cls, user, **kwargs):
        return cls(user_id=user.id, deployment=user.deployment, **kwargs)


class UserJoinedEvent(UserEvent):
    '''
    A user completed the registration process and joined the network.
    '''

    __mapper_args__ = {
        'polymorphic_identity': 'user_joined_event'
    }


class SharedMessageEvent(UserEvent):
    '''
    A message shared by a user with the network.
    '''

    __tablename__ = 'shared_messages'

    id = Column(types.Integer, ForeignKey('user_events.id'), primary_key=True)

    message = Column(types.Text)

    __mapper_args__ = {
        'polymorphic_identity': 'shared_message'
    }


class Noi1MigrationInfo(db.Model):
    __tablename__ = 'noi1_migration_info'

    id = Column(types.Integer, primary_key=True)
    user_id = Column(types.Integer, ForeignKey('users.id'))
    user = orm.relationship(
        'User',
        backref=orm.backref('noi1_migration_info', cascade='all,delete-orphan', uselist=False)
    )

    noi1_userid = Column(types.String)
    noi1_json = Column(types.Text)
    email_sent_at = Column(types.DateTime())
