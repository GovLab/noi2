'''
NoI Utils

Utility Functions
'''

from app import QUESTIONS_BY_ID
import csv


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
    number of matched questions, where the first element is the name of the
    questionnaire and the second element is a list (in no particular order) of
    the the matched quesiton IDs.
    """

    def __init__(self, user, question_ids):
        """
        `user`: a user model
        `question_ids`: a list of question ids that this User is matched to
        """
        questionnaires = {}
        for question_id in question_ids:
            question = QUESTIONS_BY_ID[question_id]
            questionnaire_name = question['questionnaire']['name']
            if questionnaire_name not in questionnaires:
                questionnaires[questionnaire_name] = set()
            questionnaires[questionnaire_name].add(question_id)

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
