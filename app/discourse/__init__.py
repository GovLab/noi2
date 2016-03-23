from flask_security.signals import user_registered, user_confirmed
from flask.ext.login import user_logged_out

from ..admin import add_admin_view
from ..signals import user_changed_profile
from . import views, sso, admin
from .config import DiscourseConfig

def init_app(app):
    config = DiscourseConfig.from_app(app)

    app.jinja_env.globals['DISCOURSE_ENABLED'] = True
    app.jinja_env.globals['discourse_url'] = config.url
    app.register_blueprint(views.views)

    add_admin_view(app, admin.DiscourseView(name='Discourse',
                                            endpoint='discourse_admin'))

    if app.config['NOI_CAN_UNCONFIRMED_USERS_FULLY_REGISTER']:
        raise Exception('Discourse support is incompatible with '
                        'NOI_CAN_UNCONFIRMED_USERS_FULLY_REGISTER')

    @user_changed_profile.connect_via(app)
    def when_user_changed_profile(sender, user, avatar_changed=False,
                                  **extra):
        sso.sync_user(user, avatar_force_update=avatar_changed)

    @user_logged_out.connect_via(app)
    def when_user_logged_out(sender, user, **extra):
        sso.logout_user(user)

    @user_registered.connect_via(app)
    def when_user_registered(sender, user, confirm_token, **extra):
        sso.sync_user(user)

    @user_confirmed.connect_via(app)
    def when_user_confirmed(sender, user, **extra):
        sso.sync_user(user)
