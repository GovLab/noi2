'''
NoI test factories

Factories to create test objects
'''

from app import QUESTIONS_BY_ID, ORG_TYPES, LOCALES
from app.models import (db, User, UserSkill, UserJoinedEvent,
                        UserExpertiseDomain, UserLanguage, Email,
                        ConnectionEvent, SharedMessageEvent)

from flask import current_app

from factory import LazyAttribute, RelatedFactory, post_generation
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyNaiveDateTime
from faker import Faker
from datetime import datetime
from random import choice, randint, sample

import logging


# Only log warnings from factoryboy, its default DEBUG statements are spammy
logger = logging.getLogger('factory')
logger.setLevel(logging.WARNING)
fake = Faker()

class SharedMessageEventFactory(SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = SharedMessageEvent
        sqlalchemy_session = db.session

    message = LazyAttribute(lambda o: fake.paragraph())


class EmailFactory(SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = Email
        sqlalchemy_session = db.session


class ConnectionEventFactory(SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = ConnectionEvent
        sqlalchemy_session = db.session


class UserJoinedEventFactory(SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = UserJoinedEvent
        sqlalchemy_session = db.session


class UserExpertiseDomainFactory(SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = UserExpertiseDomain
        sqlalchemy_session = db.session

    name = LazyAttribute(lambda o: choice(current_app.config.get('DOMAINS', [])))


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

    joined = RelatedFactory(UserJoinedEventFactory, 'user')

    position = LazyAttribute(lambda o: fake.job())
    organization = LazyAttribute(lambda o: fake.company())
    organization_type = FuzzyChoice(ORG_TYPES.keys())

    country = LazyAttribute(lambda o: fake.country_code())
    city = LazyAttribute(lambda o: fake.city())

    projects = LazyAttribute(lambda o: fake.paragraph())
    tutorial_step = 3

    @post_generation
    def expertise_domains(self, create, extracted, **kwargs): #pylint: disable=unused-argument
        if not create:
            return

        if extracted is not None:
            for expertise_domain in extracted:
                expertise_domain.user = self
            return

        else:
            domains = current_app.config.get('DOMAINS', [])
            for expertise_domain in sample(domains, randint(0, len(domains))):
                self.expertise_domains.append(
                    UserExpertiseDomainFactory.create(user_id=self.id,
                                                      name=expertise_domain))

    @post_generation
    def languages(self, create, extracted, **kwargs): #pylint: disable=unused-argument
        if not create:
            return

        if extracted is not None:
            for language in extracted:
                language.user = self
            return

        else:
            for locale in sample(LOCALES, randint(0, len(LOCALES))):
                self.languages.append(
                    UserLanguageFactory.create(user_id=self.id,
                                               locale=locale))

    @post_generation
    def skills(self, create, extracted, **kwargs): #pylint: disable=unused-argument
        if not create:
            return

        if extracted is not None:
            for skill in extracted:
                skill.user = self
            return

        else:
            question_ids = QUESTIONS_BY_ID.keys()
            for question_id in sample(question_ids, randint(0, len(question_ids))):
                self.skills.append(
                    UserSkillFactory.create(user_id=self.id,
                                            name=question_id))

    @post_generation
    def connections(self, create, extracted, **kwargs): #pylint: disable=unused-argument
        if not create:
            return

        if extracted is not None:
            for connection in extracted:
                connection.user = self
            return

        else:
            max_connection_events = 5
            max_emails_per_connection = 5

            users = User.query_in_deployment().all()
            for _ in xrange(0, randint(0, max_connection_events)):

                users_to_connect = set()
                for _ in xrange(0, randint(1, max_emails_per_connection)):
                    users_to_connect.add(choice(users))

                connection = ConnectionEventFactory.create()
                for u in users_to_connect:
                    EmailFactory.create(from_user_id=self.id,
                                        to_user_id=u.id,
                                        connection_event=connection)
                connection.set_total_connections()

    @post_generation
    def messages(self, create, extracted, **kwargs): #pylint: disable=unused-argument
        if not create:
            return

        if extracted is not None:
            for message in extracted:
                message.user = self
            return

        else:
            max_messages = 3
            for _ in xrange(0, randint(0, max_messages)):
                SharedMessageEventFactory.create(user_id=self.id)
