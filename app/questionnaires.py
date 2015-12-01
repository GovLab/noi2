import yaml
import json
from slugify import slugify
from copy import deepcopy

class Questionnaires(list):
    def __init__(self, source_list=None):
        list.__init__(self)

        if source_list is None:
            source_list = yaml.load(open('/noi/app/data/questions.yaml'))

        self[:] = deepcopy(source_list)

        by_id = {}
        questions_by_id = {}

        self.by_id = by_id
        self.questions_by_id = questions_by_id

        for questionnaire in self:
            by_id[questionnaire['id']] = questionnaire
            question_texts = {}
            area_questions = []
            questionnaire['questions'] = area_questions
            for topic in questionnaire.get('topics', []):
                for question in topic['questions']:
                    if question['question'] in question_texts:
                        raise Exception("Duplicate question text {}".\
                                        format(repr(question['question'])))
                    else:
                        question_texts[question['question']] = True
                    question_id = slugify('_'.join([questionnaire['id'],
                                                    topic['topic'],
                                                    question['label']]))
                    question['id'] = question_id
                    question['area_id'] = questionnaire['id']
                    question['topic'] = topic['topic']
                    question['questionnaire'] = questionnaire
                    if question_id in questions_by_id:
                        raise Exception("Duplicate skill id {}".\
                                        format(question_id))
                    else:
                        questions_by_id[question_id] = question
                        area_questions.append(question)

    def get_question_id_changes(self, other_questionnaires):
        '''
        Given another Questionnaires collection, returns a mapping from our
        question IDs to the other's question IDs.

        Between the two collections of Questionnaires, the following
        must remain the same:

        * Questionnaire IDs
        * Question text within each questionnaire
        '''

        result = {}
        for questionnaire in self:
            qid = questionnaire['id']
            other_qnaire = other_questionnaires.by_id[qid]

            txt1 = [q['question'] for q in questionnaire['questions']]
            txt2 = [q['question'] for q in other_qnaire['questions']]

            if txt1 != txt2:
                raise Exception('Question text in questionnaires differs')

            for question in questionnaire['questions']:
                oq = [oq for oq in other_qnaire['questions']
                      if oq['question'] == question['question']][0]
                if question['id'] != oq['id']:
                    if oq['id'] in self.questions_by_id:
                        raise Exception("Duplicate skill id {}".\
                                        format(oq['id']))
                    result[question['id']] = oq['id']

        return result

    def generate_question_id_migration_script(self, other_questionnaires):
        '''
        Like get_question_id_changes() but returns an Alembic migration
        script to implement the changes.
        '''

        changes = self.get_question_id_changes(other_questionnaires)
        changes = json.dumps(
            changes,
            sort_keys=True,
            indent=4
        )
        return QUESTION_ID_MIGRATION_SCRIPT % changes


QUESTION_ID_MIGRATION_SCRIPT = """\
from alembic import op
import sqlalchemy as sa

QUESTION_ID_CHANGES = %s

user_skills = sa.sql.table('user_skills', sa.sql.column('name', sa.String))

def rename_user_skill(from_id, to_id):
    op.execute(
        user_skills.update().\\
            where(user_skills.c.name == op.inline_literal(from_id)).\\
            values({'name': op.inline_literal(to_id)})
        )

def upgrade():
    for from_id, to_id in QUESTION_ID_CHANGES.items():
        rename_user_skill(from_id, to_id)

def downgrade():
    for to_id, from_id in QUESTION_ID_CHANGES.items():
        rename_user_skill(from_id, to_id)
"""
