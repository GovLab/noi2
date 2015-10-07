from app.models import db, User, UserSkill

from flask import current_app
from flask_security.utils import encrypt_password
from sqlalchemy.exc import IntegrityError

import json
import datetime
import factory


#def load_fixture(filename='sample_users.json', password='password'):
#    """
#    Populate DB from fixture data.
#    """
#
#    fixture_data = json.load(open('/noi/fixtures/%s' % filename, 'r'))
#    for i, user_data in enumerate(fixture_data):
#        skills = user_data.pop('skills')
#
#        for date_key in ['confirmed_at']:
#            user_data[date_key] = datetime.datetime.strptime(
#                user_data[date_key],
#                '%Y-%m-%d'
#            )
#
#        user = User(password=password, active=True, **user_data)
#        db.session.add(user)
#        try:
#            db.session.commit()
#            for name, level in skills.iteritems():
#                user.set_skill(name, level)
#            db.session.commit()
#        except IntegrityError:
#            current_app.logger.debug("Could not add user %s" % \
#                                     user_data['email'])
#            db.session.rollback()


class UserFactory(factory.alchemy.SQLAlchemyModelFactory): # pylint: disable=no-init,too-few-public-methods

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        models = User
        sqlalchemy_session = db.session

    password = encrypt_password('foobar')
    active = True


class UserSkillFactory(factory.alchemy.SQLAlchemyModelFactory): # pylint: disable=no-init,too-few-public-methods

    class Meta:  # pylint: disable=old-style-class,no-init,too-few-public-methods
        models = UserSkill
        sqlalchemy_session = db.session

def outsider_jones():
    return UserFactory.create(
        first_name="outsider",
        last_name="jones",
        email="sly@stone.com",
        confirmed_at="2010-01-01",
        deployment="sword_coast",
        skills=[
            UserSkillFactory.create(name="opendata-open-data-policy-core-mission", level=2),
            UserSkillFactory.create(name="opendata-open-data-policy-sensitive-vs-non-sensitive", level=2),
            UserSkillFactory.create(name="opendata-open-data-policy-crafting-an-open-data-policy", level=2),
            UserSkillFactory.create(name="opendata-open-data-policy-getting-public-input", level=2),
            UserSkillFactory.create(name="opendata-open-data-policy-getting-org-approval", level=2),
            UserSkillFactory.create(name="opendata-implementing-an-open-data-program-scraping-open-data", level=2),
            UserSkillFactory.create(name="opendata-implementing-an-open-data-program-making-machine-readable", level=2),
            UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-formats", level=-1),
            UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-license", level=-1),
            UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-standards", level=-1),
            UserSkillFactory.create(name="opendata-implementing-an-open-data-program-managing-open-data", level=-1),
            UserSkillFactory.create(name="opendata-implementing-an-open-data-program-frequency-of-release", level=-1),
            UserSkillFactory.create(name="opendata-implementing-an-open-data-program-data-quality-and-integrity", level=-1)
        ])
#
#sly_stone = UserFactory.create(
#    first_name="outsider",
#    last_name="jones",
#    email="sly@stone.com",
#    confirmed_at="2010-01-01",
#    deployment="sword_coast",
#    skills=[
#        UserSkillFactory.create(name="opendata-open-data-policy-core-mission", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-sensitive-vs-non-sensitive", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-crafting-an-open-data-policy", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-getting-public-input", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-getting-org-approval", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-scraping-open-data", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-making-machine-readable", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-formats", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-license", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-standards", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-managing-open-data", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-frequency-of-release", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-data-quality-and-integrity", level=-1)
#    ]
#outsider_jones = UserFactory.create(
#    first_name="outsider",
#    last_name="jones",
#    email="sly@stone.com",
#    confirmed_at="2010-01-01",
#    deployment="sword_coast",
#    skills=[
#        UserSkillFactory.create(name="opendata-open-data-policy-core-mission", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-sensitive-vs-non-sensitive", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-crafting-an-open-data-policy", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-getting-public-input", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-getting-org-approval", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-scraping-open-data", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-making-machine-readable", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-formats", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-license", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-standards", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-managing-open-data", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-frequency-of-release", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-data-quality-and-integrity", level=-1)
#    ]
#outsider_jones = UserFactory.create(
#    first_name="outsider",
#    last_name="jones",
#    email="sly@stone.com",
#    confirmed_at="2010-01-01",
#    deployment="sword_coast",
#    skills=[
#        UserSkillFactory.create(name="opendata-open-data-policy-core-mission", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-sensitive-vs-non-sensitive", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-crafting-an-open-data-policy", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-getting-public-input", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-getting-org-approval", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-scraping-open-data", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-making-machine-readable", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-formats", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-license", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-standards", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-managing-open-data", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-frequency-of-release", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-data-quality-and-integrity", level=-1)
#    ]
#outsider_jones = UserFactory.create(
#    first_name="outsider",
#    last_name="jones",
#    email="sly@stone.com",
#    confirmed_at="2010-01-01",
#    deployment="sword_coast",
#    skills=[
#        UserSkillFactory.create(name="opendata-open-data-policy-core-mission", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-sensitive-vs-non-sensitive", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-crafting-an-open-data-policy", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-getting-public-input", level=2),
#        UserSkillFactory.create(name="opendata-open-data-policy-getting-org-approval", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-scraping-open-data", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-making-machine-readable", level=2),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-formats", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-license", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-open-data-standards", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-managing-open-data", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-frequency-of-release", level=-1),
#        UserSkillFactory.create(name="opendata-implementing-an-open-data-program-data-quality-and-integrity", level=-1)
#    ]
