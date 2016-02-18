import json

from werkzeug.wrappers import Request, Response
from flask import request, current_app, abort
from flask_login import current_user
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
import flask_wtf
from wtforms import TextField

from .models import User, db
from . import stats

NAME = 'NoI Admin'

class PrefixedHttpBasicAuthMiddleware(object):
    '''
    Protect all paths starting with a given prefix behind HTTP Basic Auth.

    Based on:

    https://github.com/mitsuhiko/werkzeug/blob/master/examples/httpbasicauth.py
    '''

    def __init__(self, app, prefix, username, password, realm):
        self.prefix = prefix
        self.username = username
        self.password = password
        self.realm = realm
        self.app = app

    def check_auth(self, username, password):
        return username == self.username and password == self.password

    def auth_required(self, request):
        return Response('Could not verify your access level for that URL.\n'
                        'You have to login with proper credentials', 401,
                        {'WWW-Authenticate': 'Basic realm="%s"' % self.realm})

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '/')
        if path.startswith(self.prefix):
            request = Request(environ)
            auth = request.authorization
            if not auth or not self.check_auth(auth.username, auth.password):
                response = self.auth_required(request)
                return response(environ, start_response)
        return self.app(environ, start_response)


class AdminPermissionRequiredMixin(object):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.is_admin()

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated():
            return current_app.login_manager.unauthorized()
        return abort(403)


class StatsView(AdminPermissionRequiredMixin, BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/stats_index.html',
                           stats=json.dumps(stats.generate(), indent=2))


class NoiModelView(AdminPermissionRequiredMixin, ModelView):
    # The latest docs for flask-admin document a SecureForm class, but
    # it doesn't seem to work, so we'll use the "old" way of enabling
    # CSRF support, documented here:
    #
    # http://flask-admin.readthedocs.org/en/v1.3.0/introduction/
    form_base_class = flask_wtf.Form

    can_delete = False
    can_create = False
    can_export = True


class UserModelView(NoiModelView):
    column_list = ('username', 'first_name', 'last_name', 'email',
                   'last_login_at', 'login_count')
    form_columns = ('username', 'first_name', 'last_name', 'email',
                    'position', 'organization', 'city', 'projects')
    column_searchable_list = ('username', 'first_name', 'last_name', 'email')

    def scaffold_form(self):
        form_class = super(UserModelView, self).scaffold_form()

        # https://github.com/flask-admin/flask-admin/issues/1134
        form_class.email = TextField('Email')

        return form_class


def init_app(app):
    admin = Admin(app, name=NAME, template_mode='bootstrap3')
    admin.add_view(UserModelView(User, db.session))
    admin.add_view(StatsView(name='Stats', endpoint='stats'))

    _init_basic_auth(app)


def _init_basic_auth(app):
    basic_auth = app.config.get('ADMIN_UI_BASIC_AUTH')
    if basic_auth:
        username, password = basic_auth.split(':')
        app.wsgi_app = PrefixedHttpBasicAuthMiddleware(
            app.wsgi_app,
            prefix='/admin/',
            username=username,
            password=password,
            realm=NAME
        )
