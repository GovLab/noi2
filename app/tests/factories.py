from app.models import db, User, UserSkill, UserJoinedEvent

from factory import alchemy, LazyAttribute, RelatedFactory
from datetime import datetime

import logging


# Only log warnings from factoryboy, its default DEBUG statements are spammy
logger = logging.getLogger('factory')
logger.setLevel(logging.WARNING)

class UserJoinedEventFactory(alchemy.SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = UserJoinedEvent
        sqlalchemy_session = db.session


class UserFactory(alchemy.SQLAlchemyModelFactory): # pylint: disable=no-init,too-few-public-methods

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = User
        sqlalchemy_session = db.session

    # Can't log in to user unless SECURITY_PASSWORD_HASH='plaintext' in the config
    password = 'foobar'
    email = LazyAttribute(lambda o: '{}.{}@fakeemail.net'.format(o.first_name,
                                                                 o.last_name))
    active = True
    confirmed_at = datetime(2010, 01, 01)
    deployment = '_default'

    joined = RelatedFactory(UserJoinedEventFactory, 'user')


class UserSkillFactory(alchemy.SQLAlchemyModelFactory): # pylint: disable=no-init,too-few-public-methods

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = UserSkill
        sqlalchemy_session = db.session
