'''

Send email notifications when specific events occur (e.g. a user registers)

'''
from app import (QUESTIONNAIRES_BY_ID, MIN_QUESTIONS_TO_JOIN, LEVELS, l10n,
    LEVELS_BY_SCORE, mail, stats, cache, blog_posts, signals)
from app.models import (db, User, UserLanguage, UserExpertiseDomain, UserConference,
    UserSkill, Event, SharedMessageEvent, Email,
    skills_to_percentages, skill_counts)
from flask_security.signals import user_registered

def init_app(app):

    @user_registered.connect_via(app)
    def when_user_registered(sender, user, confirm_token, **extra):
        current_app.logger.info(repr(user))
        site_url = 'https://%s' % current_app.config['NOI_DEPLOY']
        sender = current_app.config['MAIL_USERNAME']
        mail.send_message(
            subject=gettext(
                "%(user)s registered on Network of "
                "Innovators!",
                user=current_user.full_name,
                ),
            body=gettext(
                "Event: %(user)s REGISTERED"
                "Build your network now at %(url)s.",
                user=current_user.full_name,
                url=site_url,
                ),
            sender=sender,
            recipients=[form.email.data]
            )