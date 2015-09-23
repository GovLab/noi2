from app.models import db, User, UserSkill

from flask import current_app
from sqlalchemy.exc import IntegrityError

import json
import datetime

def load_fixture(filename='sample_users.json', password='password'):
    """
    Populate DB from fixture data.
    """

    fixture_data = json.load(open('/noi/fixtures/%s' % filename, 'r'))
    for i, user_data in enumerate(fixture_data):
        skills = user_data.pop('skills')

        for date_key in ['confirmed_at']:
            user_data[date_key] = datetime.datetime.strptime(
                user_data[date_key],
                '%Y-%m-%d'
            )

        user = User(password=password, active=True, **user_data)
        for name, level in skills.iteritems():
            skill = UserSkill(name=name, level=level)
            user.skills.append(skill)
            db.session.add(skill)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            current_app.logger.debug("Could not add user %s" % \
                                     user_data['email'])
            db.session.rollback()
