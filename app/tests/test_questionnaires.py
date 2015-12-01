from unittest import TestCase
from copy import deepcopy

from app.questionnaires import Questionnaires

RAW_DATA = [
    {
        'id': 'foo',
        'topics': [{
            'topic': 'bar',
            'questions': [
                {
                    'label': 'baz'
                },
            ]
        }]
    },
]

class QuestionnairesTests(TestCase):
    def test_load_from_yaml_by_default(self):
        q = Questionnaires()
        self.assertTrue(q.by_id['opendata'])

    def test_by_id_works(self):
        q = Questionnaires(RAW_DATA)
        self.assertTrue(q.by_id['foo'])

    def test_questions_by_id_works(self):
        q = Questionnaires(RAW_DATA)
        self.assertTrue(q.questions_by_id['foo-bar-baz'])

    def test_error_raised_on_duplicate_skill_id(self):
        raw_data = deepcopy(RAW_DATA)
        raw_data[0]['topics'][0]['questions'].append({
            'label': 'baz'
        })

        with self.assertRaisesRegexp(Exception,
                                     'Duplicate skill id foo-bar-baz'):
            q = Questionnaires(raw_data)
