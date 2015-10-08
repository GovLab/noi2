'''
NoI Factory

Creates the app
'''

from flask import Flask, current_app
#from flask.ext.uploads import configure_uploads
from flask.ext.babel import get_locale
from flask_security import SQLAlchemyUserDatastore, user_registered
from flask_security.utils import get_identity_attributes

from app import (csrf, cache, mail, bcrypt, s3, assets, security,
                 babel, celery, alchemydumps, sass,
                 QUESTIONNAIRES, NOI_COLORS, LEVELS, ORG_TYPES, QUESTIONS_BY_ID)
from app.config.schedule import CELERYBEAT_SCHEDULE
from app.forms import (NOIForgotPasswordForm,
                       NOIResetPasswordForm, NOIChangePasswordForm,
                       NOIRegisterForm)
from app.models import db, User, Role
from app.views import views
from app import style_guide

from sqlalchemy.orm.exc import NoResultFound

from celery import Task
from slugify import slugify
import yaml
import flask_babel

def lazy_gettext(string):
    '''
    Like flask_babel's lazy_gettext, but doesn't interpolate strings. This is
    required for integration with flask_security, which does its
    own string interpolation but doesn't support i18n.

    For more information, see: https://github.com/GovLab/noi2/issues/41
    '''

    from speaklater import make_lazy_string

    def gettext_no_interpolate(string):
        t = flask_babel.get_translations()
        if t is None:
            return string
        return t.ugettext(string)

    return make_lazy_string(gettext_no_interpolate, string)


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

def create_app(config=None): #pylint: disable=too-many-statements
    '''
    Create an instance of the app.
    '''
    app = Flask(__name__)

    with open('/noi/app/config/config.yml', 'r') as config_file:
        app.config.update(yaml.load(config_file))

    app.config['CELERYBEAT_SCHEDULE'] = CELERYBEAT_SCHEDULE

    if config is None:
        try:
            with open('/noi/app/config/local_config.yml', 'r') as config_file:
                app.config.update(yaml.load(config_file))
        except IOError:
            app.logger.warn("No local_config.yml file")
    else:
        app.config.update(config)

    # Confirming email is currently unsupported.
    app.config['SECURITY_CONFIRMABLE'] = False

    with open('/noi/app/data/deployments.yaml') as deployments_yaml:
        deployments = yaml.load(deployments_yaml)

    app.config['SECURITY_MSG_UNAUTHORIZED'] = (
        lazy_gettext('You do not have permission to view this resource.'), 'error')
    app.config['SECURITY_MSG_EMAIL_ALREADY_ASSOCIATED'] = (
        lazy_gettext('%(email)s is already associated with an account.'), 'error')
    app.config['SECURITY_MSG_PASSWORD_MISMATCH'] = (
        lazy_gettext('Password does not match'), 'error')
    app.config['SECURITY_MSG_RETYPE_PASSWORD_MISMATCH'] = (
        lazy_gettext('Passwords do not match'), 'error')
    app.config['SECURITY_MSG_INVALID_REDIRECT'] = (
        lazy_gettext('Redirections outside the domain are forbidden'), 'error')
    app.config['SECURITY_MSG_PASSWORD_RESET_REQUEST'] = (
        lazy_gettext('Instructions to reset your password have been sent to %(email)s.'), 'info')
    app.config['SECURITY_MSG_PASSWORD_RESET_EXPIRED'] = (
        lazy_gettext('You did not reset your password within %(within)s. New '
                     'instructions have been sent to %(email)s.'), 'error')
    app.config['SECURITY_MSG_INVALID_RESET_PASSWORD_TOKEN'] = (
        lazy_gettext('Invalid reset password token.'), 'error')
    app.config['SECURITY_MSG_LOGIN_EXPIRED'] = (
        lazy_gettext('You did not login within %(within)s. New instructions to '
                     'login have been sent to %(email)s.'), 'error')
    app.config['SECURITY_MSG_LOGIN_EMAIL_SENT'] = (
        lazy_gettext('Instructions to login have been sent to %(email)s.'), 'success')
    app.config['SECURITY_MSG_INVALID_LOGIN_TOKEN'] = (
        lazy_gettext('Invalid login token.'), 'error')
    app.config['SECURITY_MSG_DISABLED_ACCOUNT'] = (
        lazy_gettext('Account is disabled.'), 'error')
    app.config['SECURITY_MSG_EMAIL_NOT_PROVIDED'] = (
        lazy_gettext('Email not provided'), 'error')
    app.config['SECURITY_MSG_INVALID_EMAIL_ADDRESS'] = (
        lazy_gettext('Invalid email address'), 'error')
    app.config['SECURITY_MSG_PASSWORD_NOT_PROVIDED'] = (
        lazy_gettext('Password not provided'), 'error')
    app.config['SECURITY_MSG_PASSWORD_NOT_SET'] = (
        lazy_gettext('No password is set for this user'), 'error')
    app.config['SECURITY_MSG_PASSWORD_INVALID_LENGTH'] = (
        lazy_gettext('Password must be at least 6 characters'), 'error')
    app.config['SECURITY_MSG_USER_DOES_NOT_EXIST'] = (
        lazy_gettext('Specified user does not exist'), 'error')
    app.config['SECURITY_MSG_INVALID_PASSWORD'] = (
        lazy_gettext('Invalid password'), 'error')
    app.config['SECURITY_MSG_PASSWORDLESS_LOGIN_SUCCESSFUL'] = (
        lazy_gettext('You have successfuly logged in.'), 'success')
    app.config['SECURITY_MSG_PASSWORD_RESET'] = (
        lazy_gettext('You successfully reset your password and you have been '
                     'logged in automatically.'), 'success')
    app.config['SECURITY_MSG_PASSWORD_IS_THE_SAME'] = (
        lazy_gettext('Your new password must be different than your previous password.'), 'error')
    app.config['SECURITY_MSG_PASSWORD_CHANGE'] = (
        lazy_gettext('You successfully changed your password.'), 'success')
    app.config['SECURITY_MSG_LOGIN'] = (
        lazy_gettext('Please log in to access this page.'), 'info')
    app.config['SECURITY_MSG_REFRESH'] = (
        lazy_gettext('Please reauthenticate to access this page.'), 'info')

    app.register_blueprint(views)
    if app.config['DEBUG']:
        app.register_blueprint(style_guide.views)

    cache.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    s3.init_app(app)
    #configure_uploads(app, (photos))

    # Setup Flask-Security
    user_datastore = DeploySQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, datastore=user_datastore,
                      register_form=NOIRegisterForm,
                      forgot_password_form=NOIForgotPasswordForm,
                      reset_password_form=NOIResetPasswordForm,
                      change_password_form=NOIChangePasswordForm)

    # This forces any "lazy strings" like those returned by
    # lazy_gettext() to be evaluated.
    app.login_manager.localize_callback = unicode

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

    app.config['DOMAINS'] = this_deployment.get('domains',
                                                default_deployment['domains'])

    app.config['CONTACT_FORM_ID'] = this_deployment.get('contact_form_id',
                                                default_deployment['contact_form_id'])

    # Constant that should be available for all templates.

    app.jinja_env.globals['get_locale'] = get_locale
    app.jinja_env.globals['NOI_DEPLOY'] = noi_deploy
    app.jinja_env.globals['ORG_TYPES'] = ORG_TYPES
    app.jinja_env.globals['NOI_COLORS'] = NOI_COLORS
    app.jinja_env.globals['LEVELS'] = LEVELS
    app.jinja_env.globals['QUESTIONS_BY_ID'] = QUESTIONS_BY_ID

    app.jinja_env.globals['ABOUT'] = this_deployment.get('about',
                                                         default_deployment['about'])

    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
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

    return app

def create_celery(app=None):
    '''
    Create celery tasks
    '''

    app = app or create_app()

    class ContextTask(Task): #pylint: disable=abstract-method
        '''
        Run tasks within app context.
        '''
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return Task.__call__(self, *args, **kwargs)


    celery.conf.update(app.config)
    celery.Task = ContextTask

    return celery

