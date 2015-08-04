'''
NoI Factory

Creates the app
'''

from flask import Flask
from flask.ext.uploads import configure_uploads
from flask.ext.security import SQLAlchemyUserDatastore

from app import (csrf, cache, mail, bcrypt, photos, s3, assets, security,
                 CONTENT, COUNTRIES, LANGS, NOI_COLORS, LEVELS, ORG_TYPES,
                 DOMAINS)
from app.models import db, User, Role
from app.views import views

from ordbok.flask_helper import FlaskOrdbok
from slugify import slugify



def create_app():
    app = Flask(__name__, template_folder="templates")

    ordbok = FlaskOrdbok(app)
    ordbok.load()

    app.config.update(ordbok)
    #app.config.update(config or {})

    app.register_blueprint(views)

    cache.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    #security.init_app(app, bcrypt)
    s3.init_app(app)
    configure_uploads(app, (photos))

    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, datastore=user_datastore)

    db.init_app(app)
    #login_manager.init_app(app)
    assets.init_app(app)

    app.jinja_env.filters['slug'] = lambda x: slugify(x, to_lower=True)
    app.jinja_env.filters['noop'] = lambda x: ''

    # Constant that should be available for all templates.
    app.jinja_env.globals['ORG_TYPES'] = ORG_TYPES
    app.jinja_env.globals['CONTENT'] = CONTENT
    app.jinja_env.globals['COUNTRIES'] = COUNTRIES
    app.jinja_env.globals['LANGS'] = LANGS
    app.jinja_env.globals['NOI_COLORS'] = NOI_COLORS
    app.jinja_env.globals['LEVELS'] = LEVELS
    app.jinja_env.globals['DOMAINS'] = DOMAINS

    return app
