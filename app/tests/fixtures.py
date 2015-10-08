from app.models import db, User, UserSkill

from flask import current_app
from factory import alchemy, LazyAttribute
#from flask_security.utils import encrypt_password
from datetime import datetime


def load_fixture():
    '''
    tmp
    '''
    outsider_jones()
    sly_stone()
    sly_stone_less()
    sly_stone_more()
    paul_lennon()
    dubya_shrub()


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


class UserSkillFactory(alchemy.SQLAlchemyModelFactory): # pylint: disable=no-init,too-few-public-methods

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        model = UserSkill
        sqlalchemy_session = db.session


def outsider_jones():
    return UserFactory.create(
        first_name="outsider",
        last_name="jones",
        email="sly@stone.com",
        deployment="sword_coast",
        skills=[UserSkillFactory.create(name=name, level=level) for name, level in [
            ("opendata-open-data-policy-core-mission", 2),
            ("opendata-open-data-policy-sensitive-vs-non-sensitive", 2),
            ("opendata-open-data-policy-crafting-an-open-data-policy", 2),
            ("opendata-open-data-policy-getting-public-input", 2),
            ("opendata-open-data-policy-getting-org-approval", 2),
            ("opendata-implementing-an-open-data-program-scraping-open-data", 2),
            ("opendata-implementing-an-open-data-program-making-machine-readable", 2),
            ("opendata-implementing-an-open-data-program-open-data-formats", -1),
            ("opendata-implementing-an-open-data-program-open-data-license", -1),
            ("opendata-implementing-an-open-data-program-open-data-standards", -1),
            ("opendata-implementing-an-open-data-program-managing-open-data", -1),
            ("opendata-implementing-an-open-data-program-frequency-of-release", -1),
            ("opendata-implementing-an-open-data-program-data-quality-and-integrity", -1)
        ]])


def sly_stone():
    return UserFactory.create(
        first_name="sly",
        last_name="stone",
        email="sly@stone.com",
        skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
            "opendata-open-data-policy-core-mission": -1,
            "opendata-open-data-policy-sensitive-vs-non-sensitive": -1,
            "opendata-open-data-policy-crafting-an-open-data-policy": -1,
            "opendata-open-data-policy-getting-public-input": -1,
            "opendata-open-data-policy-getting-org-approval": -1,
            "opendata-implementing-an-open-data-program-scraping-open-data": -1,
            "opendata-implementing-an-open-data-program-making-machine-readable": -1,
            "opendata-implementing-an-open-data-program-open-data-formats": -1,
            "opendata-implementing-an-open-data-program-open-data-license": -1,
            "opendata-implementing-an-open-data-program-open-data-standards": -1,
            "opendata-implementing-an-open-data-program-managing-open-data": -1,
            "opendata-implementing-an-open-data-program-frequency-of-release": -1,
            "opendata-implementing-an-open-data-program-data-quality-and-integrity": -1
        }.items()])

def sly_stone_more():
    return UserFactory.create(
        first_name="sly",
        last_name="stone-more-knowledgeable",
        email="sly@stone-more.com",
        skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
            "opendata-open-data-policy-core-mission": 2,
            "opendata-open-data-policy-sensitive-vs-non-sensitive": 2,
            "opendata-open-data-policy-crafting-an-open-data-policy": 2,
            "opendata-open-data-policy-getting-public-input": 2,
            "opendata-open-data-policy-getting-org-approval": 2,
            "opendata-implementing-an-open-data-program-scraping-open-data": -1,
            "opendata-implementing-an-open-data-program-making-machine-readable": -1,
            "opendata-implementing-an-open-data-program-open-data-formats": -1,
            "opendata-implementing-an-open-data-program-open-data-license": -1,
            "opendata-implementing-an-open-data-program-open-data-standards": -1,
            "opendata-implementing-an-open-data-program-managing-open-data": -1,
            "opendata-implementing-an-open-data-program-frequency-of-release": -1,
            "opendata-implementing-an-open-data-program-data-quality-and-integrity": -1
        }.items()])

def sly_stone_less():
    return UserFactory.create(
        first_name="sly",
        last_name="stone-less-knowledgeable",
        email="sly@stone-less-knowledgeable.com",
        skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
            "opendata-implementing-an-open-data-program-open-data-standards": -1,
            "opendata-implementing-an-open-data-program-managing-open-data": -1,
            "opendata-implementing-an-open-data-program-frequency-of-release": -1,
            "opendata-implementing-an-open-data-program-data-quality-and-integrity": -1
        }.items()])

def paul_lennon():
    return UserFactory.create(
        first_name="paul",
        last_name="lennon",
        email="paul@lennon.com",
        skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
            "opendata-open-data-policy-core-mission": 5,
            "opendata-open-data-policy-sensitive-vs-non-sensitive": 5,
            "opendata-open-data-policy-crafting-an-open-data-policy": 5,
            "opendata-open-data-policy-getting-public-input": 5,
            "opendata-open-data-policy-getting-org-approval": 5,
            "opendata-implementing-an-open-data-program-scraping-open-data": 5,
            "opendata-implementing-an-open-data-program-making-machine-readable": 5,
            "opendata-implementing-an-open-data-program-open-data-formats": 5,
            "opendata-implementing-an-open-data-program-open-data-license": 5,
            "opendata-implementing-an-open-data-program-open-data-standards": 5,
            "opendata-implementing-an-open-data-program-managing-open-data": 5,
            "opendata-implementing-an-open-data-program-frequency-of-release": 5,
            "opendata-implementing-an-open-data-program-data-quality-and-integrity": 5
        }.items()])

def dubya_shrub():
    return UserFactory.create(
        first_name="dubya",
        last_name="shrub",
        email="dubya@shrub.com",
        skills=[UserSkillFactory.create(name=name, level=level) for name, level in {
            "opendata-open-data-policy-core-mission": 1,
            "opendata-open-data-policy-sensitive-vs-non-sensitive": 1,
            "opendata-open-data-policy-crafting-an-open-data-policy": 1,
            "opendata-open-data-policy-getting-public-input": 1,
            "opendata-open-data-policy-getting-org-approval": 1,
            "opendata-implementing-an-open-data-program-scraping-open-data": 1,
            "opendata-implementing-an-open-data-program-making-machine-readable": 1,
            "opendata-implementing-an-open-data-program-open-data-formats": 1,
            "opendata-implementing-an-open-data-program-open-data-license": 1,
            "opendata-implementing-an-open-data-program-open-data-standards": 1,
            "opendata-implementing-an-open-data-program-managing-open-data": 1,
            "opendata-implementing-an-open-data-program-frequency-of-release": 1,
            "opendata-implementing-an-open-data-program-data-quality-and-integrity": 1
        }.items()])
