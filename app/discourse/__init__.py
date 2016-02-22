from flask_security.signals import user_registered
from flask.ext.login import user_logged_out

from . import views, sso
from .config import DiscourseConfig

def init_app(app):
    config = DiscourseConfig.from_app(app)

    app.jinja_env.globals['DISCOURSE_ENABLED'] = True
    app.jinja_env.globals['discourse_url'] = config.url
    app.register_blueprint(views.views)

    @user_logged_out.connect_via(app)
    def when_user_logged_out(sender, user, **extra):
        sso.logout_user(user)

    @user_registered.connect_via(app)
    def when_user_registered(sender, user, confirm_token, **extra):
        sso.sync_user(user)
