'''
NoI Factory

Creates the app
'''

from flask import Flask
from flask.ext.uploads import configure_uploads

from app import (csrf, cache, mail, bcrypt, security, photos, s3, assets)
from app.models import db

from ordbok.flask_helper import FlaskOrdbok


def create_app(config=None):
    app = Flask(__name__, template_folder="templates")

    ordbok = FlaskOrdbok(app)
    ordbok.load()

    app.config.update(ordbok)
    app.config.update(config or {})

    cache.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    security.init_app(app, bcrypt)
    s3.init_app(app)
    configure_uploads(app, (photos))
    db.init_app(app)
    #login_manager.init_app(app)
    assets.init_app(app)
