'''
NoI test factories

Factories to create test objects
'''

from app import QUESTIONS_BY_ID, ORG_TYPES, LOCALES
from app.models import (db, User, UserSkill, UserJoinedEvent,
                        UserExpertiseDomain, UserLanguage)

from flask import current_app

from factory import LazyAttribute, RelatedFactory, post_generation
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyNaiveDateTime
from faker import Faker
from datetime import datetime
from random import choice, randint

import logging


# Only log warnings from factoryboy, its default DEBUG statements are spammy
logger = logging.getLogger('factory')
logger.setLevel(logging.WARNING)
fake = Faker()

class UserJoinedEventFactory(SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = UserJoinedEvent
        sqlalchemy_session = db.session


class UserExpertiseDomainFactory(SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = UserExpertiseDomain
        sqlalchemy_session = db.session

    name = LazyAttribute(lambda o: choice(current_app.config['DOMAINS']))


class UserLanguageFactory(SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = UserLanguage
        sqlalchemy_session = db.session

    locale = FuzzyChoice(LOCALES)


class UserSkillFactory(SQLAlchemyModelFactory): # pylint: disable=no-init,too-few-public-methods

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = UserSkill
        sqlalchemy_session = db.session

    name = FuzzyChoice(QUESTIONS_BY_ID.keys())
    #level = FuzzyChoice([l['score'] for l in LEVELS.values()])
    level = FuzzyChoice([-1, 1, 2, 5])


class UserFactory(SQLAlchemyModelFactory): # pylint: disable=no-init,too-few-public-methods

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = User
        sqlalchemy_session = db.session

    first_name = LazyAttribute(lambda o: fake.first_name())
    last_name = LazyAttribute(lambda o: fake.last_name())

    # Can't log in to user unless SECURITY_PASSWORD_HASH='plaintext' in the config
    password = 'foobar'
    email = LazyAttribute(lambda o: '{}.{}@fakeemail.net'.format(o.first_name,
                                                                 o.last_name))
    active = True
    confirmed_at = FuzzyNaiveDateTime(datetime(2015, 1, 1))
    deployment = '_default'

    joined = RelatedFactory(UserJoinedEventFactory, 'user')

    organization = LazyAttribute(lambda o: fake.company())
    organization_type = FuzzyChoice(ORG_TYPES.values())

    country = LazyAttribute(lambda o: fake.country())
    city = LazyAttribute(lambda o: fake.city())

    projects = LazyAttribute(lambda o: fake.paragraph())
    tutorial_step = 3

    @post_generation
    def gen_expertise_domains(self, create, extracted, **kwargs): #pylint: disable=unused-argument
        if not create:
            return

        if extracted:
            return

        else:
            for _ in xrange(0, randint(0, 10)):
                self.expertise_domains.append(
                    UserExpertiseDomainFactory.create(user_id=self.id))

    @post_generation
    def gen_languages(self, create, extracted, **kwargs): #pylint: disable=unused-argument
        if not create:
            return

        if extracted:
            return

        else:
            for _ in xrange(0, randint(0, 10)):
                self.languages.append(
                    UserLanguageFactory.create(user_id=self.id))

    @post_generation
    def gen_skills(self, create, extracted, **kwargs): #pylint: disable=unused-argument
        if not create:
            return

        if extracted:
            return

        else:
            for _ in xrange(0, randint(0, 10)):
                self.skills.append(
                    UserSkillFactory.create(user_id=self.id))
