from . import views

def init_app(app):
    app.jinja_env.globals['DISCOURSE_ENABLED'] = True
    app.register_blueprint(views.views)
