'''
NoI Factory

Creates the app
'''

from flask import Flask, current_app
from flask.ext.babel import get_locale
from flask_security import SQLAlchemyUserDatastore, user_registered
from flask_security.utils import get_identity_attributes
from werkzeug.contrib.fixers import ProxyFix

from app import (csrf, cache, mail, bcrypt, s3, assets, security, admin,
                 babel, alchemydumps, sass, email_errors, csp, oauth,
                 linkedin,
                 QUESTIONNAIRES, NOI_COLORS, LEVELS, ORG_TYPES,
                 QUESTIONS_BY_ID, LEVELS_BY_SCORE, QUESTIONNAIRES_BY_ID)
from app.forms import (NOIForgotPasswordForm, NOILoginForm,
                       NOIResetPasswordForm, NOIChangePasswordForm,
                       NOIConfirmRegisterForm, NOISendConfirmationForm)
from app.models import db, User, Role
from app.views import views
from app.utils import get_nopic_avatar
from app import style_guide, l10n

from sqlalchemy.orm.exc import NoResultFound

from slugify import slugify
import yaml
import json
import os


# App config vars that are exposed to client-side JavaScript code.
EXPOSED_APP_CONFIG_VARS = [
  'DEBUG',
  'PINGDOM_RUM_ID',
  'GA_TRACKING_CODE'
]

class DeploySQLAlchemyUserDatastore(SQLAlchemyUserDatastore):
    '''
    Subclass of SQLAlchemyUserDatastore that overrides `get_user` to take app
    domain into account.
    '''

    def get_user(self, identifier):
        '''
        Get user by email or id, for this deployment.
        '''
        if self._is_numeric(identifier):
            return self.user_model.query.get(identifier)
        for attr in get_identity_attributes():
            query = getattr(self.user_model, attr).ilike(identifier)
            rv = self.user_model.query.filter_by(
                deployment=current_app.config['NOI_DEPLOY']).filter(query).first()
            if rv is not None:
                return rv

def configure_from_os_environment(config, env=os.environ):
    if not config.get('MAIL_SERVER') and env.get('MAIL_SERVER'):
        config['MAIL_SERVER'] = env['MAIL_SERVER']
        config['MAIL_PORT'] = int(env['MAIL_PORT'])

def create_app(config=None): #pylint: disable=too-many-statements
    '''
    Create an instance of the app.
    '''
    app = Flask(__name__)

    with open('/noi/app/config/config.yml', 'r') as config_file:
        app.config.update(yaml.load(config_file))

    if config is None:
        try:
            with open('/noi/app/config/local_config.yml', 'r') as config_file:
                app.config.update(yaml.load(config_file))
        except IOError:
            app.logger.warn("No local_config.yml file")
        configure_from_os_environment(app.config)
    else:
        app.config.update(config)

    with open('/noi/app/data/deployments.yaml') as deployments_yaml:
        deployments = yaml.load(deployments_yaml)

    l10n.configure_app(app)

    app.register_blueprint(views)
    if app.config['DEBUG']:
        app.register_blueprint(style_guide.views)

        try:
            from flask_debugtoolbar import DebugToolbarExtension
            debug_toolbar = DebugToolbarExtension(app)
        except:
            app.logger.exception('Initialization of Flask-DebugToolbar '
                                 'failed.')

    if not app.config['DEBUG'] and app.config.get('ADMINS'):
        email_errors.init_app(app)

    oauth.init_app(app)
    if 'LINKEDIN' in app.config:
        app.jinja_env.globals['LINKEDIN_ENABLED'] = True
        app.register_blueprint(linkedin.views)

    cache.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    s3.init_app(app)

    # Setup Flask-Security
    user_datastore = DeploySQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, datastore=user_datastore,
                      login_form=NOILoginForm,
                      confirm_register_form=NOIConfirmRegisterForm,
                      forgot_password_form=NOIForgotPasswordForm,
                      reset_password_form=NOIResetPasswordForm,
                      change_password_form=NOIChangePasswordForm,
                      send_confirmation_form=NOISendConfirmationForm)

    db.init_app(app)
    alchemydumps.init_app(app, db)
    #login_manager.init_app(app)
    assets.init_app(app)

    app.jinja_env.filters['slug'] = lambda x: slugify(x).lower()

    noi_deploy = app.config['NOI_DEPLOY']
    if noi_deploy == '_default':
        app.logger.warn('No NOI_DEPLOY found in config, deploy-specific '
                        'attributes like the About page, custom domains and '
                        'logos will be missing.')
    this_deployment = deployments.get(noi_deploy, deployments['_default'])
    default_deployment = deployments['_default']
    if 'locale' in this_deployment:
        app.config['BABEL_DEFAULT_LOCALE'] = this_deployment['locale']
    app.config['SEARCH_DEPLOYMENTS'] = this_deployment.get('searches', []) or []
    app.config['SEARCH_DEPLOYMENTS'].append(noi_deploy)
    babel.init_app(app)
    l10n.init_app(app)
    admin.init_app(app)

    app.config['DOMAINS'] = this_deployment.get('domains',
                                                default_deployment['domains'])

    app.config['CONTACT_FORM_ID'] = this_deployment.get('contact_form_id',
                                                default_deployment['contact_form_id'])

    # Constants that should be available for all templates.

    global_config_json = {}

    for exposed_var in EXPOSED_APP_CONFIG_VARS:
        if exposed_var in app.config:
            global_config_json[exposed_var] = app.config[exposed_var]

    global_config_json = json.dumps(global_config_json)

    app.jinja_env.globals['global_config_json'] = global_config_json
    app.jinja_env.globals['get_locale'] = get_locale
    app.jinja_env.globals['get_nopic_avatar'] = get_nopic_avatar
    app.jinja_env.globals['NOI_DEPLOY'] = noi_deploy
    app.jinja_env.globals['ORG_TYPES'] = ORG_TYPES
    app.jinja_env.globals['NOI_COLORS'] = NOI_COLORS
    app.jinja_env.globals['LEVELS'] = LEVELS
    app.jinja_env.globals['LEVELS_BY_SCORE'] = LEVELS_BY_SCORE
    app.jinja_env.globals['QUESTIONS_BY_ID'] = QUESTIONS_BY_ID
    app.jinja_env.globals['QUESTIONNAIRES_BY_ID'] = QUESTIONNAIRES_BY_ID

    app.jinja_env.globals['ABOUT'] = this_deployment.get('about',
                                                         default_deployment['about'])

    if not app.config.get('MAIL_SERVER'):
        app.logger.warn('No MAIL_SERVER found in config, password reset will '
                        'not work.')

    if not app.config.get('GA_TRACKING_CODE'):
        app.logger.warn('No GA_TRACKING_CODE found in config, analytics will'
                        ' not work.')

    # Order questionnaires for deployments that want custom order.
    questionnaire_order = this_deployment.get('questions',
                                              default_deployment['questions'])
    if questionnaire_order:
        new_order = []
        for topic in questionnaire_order:
            if isinstance(topic, basestring):
                q_id = topic
                custom_description = None
            else:
                q_id = topic.keys()[0]
                custom_description = topic[q_id].get('description')

            try:
                questionnaire = [q for q in QUESTIONNAIRES if q['id'] == q_id][0]
                if custom_description:
                    questionnaire['description'] = custom_description
                new_order.append(questionnaire)
                #new_order.append(filter(lambda q: q['id'] == q_id, QUESTIONNAIRES)[0])
            except IndexError:
                raise Exception('Cannot find questionairre ID "{}", aborting'.format(
                    q_id))
        app.jinja_env.globals['QUESTIONNAIRES'] = new_order
    else:
        app.jinja_env.globals['QUESTIONNAIRES'] = QUESTIONNAIRES

    # Signals
    @user_registered.connect_via(app)
    def add_deployment_role(sender, **kwargs):
        """
        Add role for this deployment whenever a new user registers.
        """
        user = kwargs['user']
        try:
            role = Role.query.filter_by(name=sender.config['NOI_DEPLOY']).one()
        except NoResultFound:
            role = Role(name=sender.config['NOI_DEPLOY'])
            db.session.add(role)

        user.roles.append(role)
        db.session.add(user)
        db.session.commit()

    sass.init_app(app)
    csp.init_app(app)

    if app.config.get('BASIC_AUTH_FORCE'):
        from flask.ext.basicauth import BasicAuth

        basic_auth = BasicAuth()
        basic_auth.init_app(app)

    app.wsgi_app = ProxyFix(app.wsgi_app)

    return app
