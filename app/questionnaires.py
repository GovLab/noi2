import yaml
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
            area_questions = []
            questionnaire['questions'] = area_questions
            for topic in questionnaire.get('topics', []):
                for question in topic['questions']:
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
