'''
NoI Utils

Utility Functions
'''

import os
import posixpath
import hashlib
import csv
from flask import current_app, url_for

from app import QUESTIONS_BY_ID


NOPIC_AVATAR_DIR = ['img', 'nopic-avatars']

def get_user_avatar_url(user, _external=False):
    if user is None:
        return get_nopic_avatar('nobody@example.com', _external=_external)
    if user.has_picture:
        return user.picture_url
    if user.linkedin and user.linkedin.picture_url:
        return user.linkedin.picture_url
    return get_nopic_avatar(user.email, _external=_external)

def get_nopic_avatar(email, _external=False):
    # TODO: We might want to cache/memoize the results of this
    # function if it becomes too resource-intensive.

    images = os.listdir(os.path.join(current_app.static_folder,
                                     *NOPIC_AVATAR_DIR))

    try:
        # http://stackoverflow.com/a/2511075/2422398
        index = int(hashlib.md5(email).hexdigest(), 16) % len(images)
    except TypeError:
        # This could be because e.g. jinja2.Undefined was passed to us.
        # Just fall-back to a reasonable default.
        index = 0

    filename = images[index]
    return url_for(
        'static',
        filename=posixpath.join(*(NOPIC_AVATAR_DIR + [filename])),
        _external=_external
    )


def csv_reader(path_to_file):
    """
    Read a CSV with headers, yielding a dict for each row.
    """
    with open(path_to_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            yield row


class UserSkillMatch(object):
    """
    An object linking a User with matched skills.

    This object exposes `user` and `questionnaires` properties.  The
    `questionnaires` property is a list of two-tuples, in descending order of
    number of matched questions, where the first element is the ID of the
    questionnaire and the second element is a list (in no particular order) of
    the the matched question IDs.
    """

    def __init__(self, user, question_ids):
        """
        `user`: a user model
        `question_ids`: a list of question ids that this User is matched to
        """
        questionnaires = {}
        for question_id in question_ids:
            question = QUESTIONS_BY_ID[question_id]
            questionnaire_id = question['questionnaire']['id']
            if questionnaire_id not in questionnaires:
                questionnaires[questionnaire_id] = set()
            questionnaires[questionnaire_id].add(question_id)

        self._user = user
        self._questionnaires = sorted(questionnaires.iteritems(),
                                      lambda a, b: len(a[1]) - len(b[1]),
                                      reverse=True)

    @property
    def user(self):
        return self._user

    @property
    def questionnaires(self):
        return self._questionnaires
