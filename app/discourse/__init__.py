from flask_security.signals import user_registered

from . import views, sso

def init_app(app):
    app.jinja_env.globals['DISCOURSE_ENABLED'] = True
    app.register_blueprint(views.views)

    @user_registered.connect_via(app)
    def when_user_registered(sender, user, confirm_token, **extra):
        sso.sync_user(user)
