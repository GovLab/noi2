from app import models, LEVELS, QUESTIONNAIRES

from sqlalchemy import func

db = models.db

def get_shared_message_count():
    return db.session.query(func.count(
        models.SharedMessageEvent.id
    )).scalar()

def get_skill_count(skill_level):
    return db.session.query(
        func.count(models.UserSkill.id)
    ).filter(models.UserSkill.level == skill_level).scalar()

def get_total_questions_answered():
    return db.session.query(func.count(models.UserSkill.id)).scalar()

def get_skill_counts():
    return {
        "learn": get_skill_count(LEVELS['LEVEL_I_WANT_TO_LEARN']['score']),
        "explain": get_skill_count(LEVELS['LEVEL_I_CAN_EXPLAIN']['score']),
        "connect": get_skill_count(LEVELS['LEVEL_I_CAN_REFER']['score']),
        "do": get_skill_count(LEVELS['LEVEL_I_CAN_DO_IT']['score'])
    }

def get_top_countries():
    count = func.count(models.User.id)
    query = db.session.query(models.User.country, count).\
        group_by(models.User.country).\
        order_by(count.desc()).\
        limit(10).all()
    return [
        ("%s (%s)" % (item[0].name, item[0].code), item[1]) for item in query
    ]

def get_avg_num_questions_answered():
    answers_per_user = db.session.query(
        func.count(models.UserSkill.id).label('num_answers')
    ).filter(models.User.id == models.UserSkill.user_id).\
      group_by(models.User)

    return float(db.session.query(
        func.avg(answers_per_user.subquery().columns.num_answers)
    ).scalar() or 0)

def get_questionnaire_counts():
    counts = {}
    for questionnaire in QUESTIONNAIRES:
        if not questionnaire['questions']: continue
        qid = questionnaire['id']
        counts[qid] = {}
        query = db.session.query(
            models.UserSkill.level,
            func.count(models.UserSkill.id)
        ).filter(models.UserSkill.name.like(qid + "_%")).\
          group_by(models.UserSkill.level)
        raw_counts = dict(query.all())
        counts[qid].update(models.scores_to_skills(raw_counts))
    return counts

def generate():
    return {
        "users": db.session.query(func.count(models.User.id)).scalar(),
        "connections": models.ConnectionEvent.connections_in_deployment(),
        "messages": get_shared_message_count(),
        "countries": get_top_countries(),
        "avg_num_questions_answered": get_avg_num_questions_answered(),
        "total_questions_answered": get_total_questions_answered(),
        "questionnaire_counts": get_questionnaire_counts(),
        "skill_counts": get_skill_counts()
    }
