'''

Send email notifications when specific events occur (e.g. a user registers)

'''
from app import (mail, stats, cache, blog_posts, signals)
from app.models import (db, User, UserLanguage, UserExpertiseDomain, UserConference,
    UserSkill, Event, SharedMessageEvent, Email)
from flask_babel import lazy_gettext, gettext
from flask_security.signals import user_registered
from signals import user_completed_registration

def init_app(app):

    @user_completed_registration.connect_via(app)
    def registration_notice(sender, user, **extra):
        # site_url = 'https://%s' % app.config['NOI_DEPLOY']
        # sender = app.config['MAIL_USERNAME']
        sender = 'noreply@networkofinnovators.org'
        mail.send_message(
            subject=gettext(
                "%(user)s registered on Network of "
                "Innovators!",
                user=user.full_name
                ),
            body=gettext(
                "%(user)s Created a new profile: "
                "\n\n"
                "\nName: %(user)s"
                "\nPosition: %(position)s"
                "\nOrganization: %(organization)s"
                "\nOrganization Type: %(organization_type)s"
                "\nCountry: %(country)s"
                "\nCity: %(city)s"
                "\n\n",
                user=user.full_name,
                position=user.position,
                organization=user.organization,
                organization_type=user.organization_type,
                country=user.country,
                city=user.city
                ),
            sender=sender,
            recipients=["admins@thegovlab.org", "noveck@thegovlab.org"]
            )