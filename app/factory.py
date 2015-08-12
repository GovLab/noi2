'''
NoI Factory

Creates the app
'''

from flask import Flask
#from flask.ext.uploads import configure_uploads
from flask_security import SQLAlchemyUserDatastore

from app import (csrf, cache, mail, bcrypt, s3, assets, security,
                 babel,
                 QUESTIONNAIRES, NOI_COLORS, LEVELS, ORG_TYPES, QUESTIONS_BY_ID)
from app.forms import RegisterForm
from app.models import db, User, Role
from app.views import views

from slugify import slugify
import yaml


def create_app():
    '''
    Create an instance of the app.
    '''
    app = Flask(__name__)

    with open('/noi/app/config/config.yml', 'r') as config_file:
        app.config.update(yaml.load(config_file))

    with open('/noi/app/config/local_config.yml', 'r') as config_file:
        app.config.update(yaml.load(config_file))

    app.register_blueprint(views)

    babel.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    #security.init_app(app, bcrypt)
    s3.init_app(app)
    #configure_uploads(app, (photos))

    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, datastore=user_datastore,
                      register_form=RegisterForm)

    db.init_app(app)
    #login_manager.init_app(app)
    assets.init_app(app)

    app.jinja_env.filters['slug'] = lambda x: slugify(x).lower()
    app.jinja_env.filters['noop'] = lambda x: ''

    noi_deploy = app.config.get('NOI_DEPLOY')
    if not noi_deploy:
        app.logger.warn('No NOI_DEPLOY found in config, deploy-specific '
                        'attributes like the About page and logos will be '
                        'missing.')

    # Constant that should be available for all templates.
    app.jinja_env.globals['ORG_TYPES'] = ORG_TYPES
    app.jinja_env.globals['QUESTIONNAIRES'] = QUESTIONNAIRES
    app.jinja_env.globals['NOI_COLORS'] = NOI_COLORS
    app.jinja_env.globals['LEVELS'] = LEVELS
    app.jinja_env.globals['QUESTIONS_BY_ID'] = QUESTIONS_BY_ID
    with open('/noi/app/data/about.yaml') as about_yaml:
        app.jinja_env.globals['ABOUT'] = yaml.load(about_yaml).get(noi_deploy)

    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
        app.logger.warn('No MAIL_SERVER found in config, password reset will '
                        'not work.')

    if not app.config.get('GA_TRACKING_CODE'):
        app.logger.warn('No GA_TRACKING_CODE found in config, analytics will'
                        ' not work.')

    return app
