from flask import redirect, request
from flask_login import current_user
from flask_security.utils import url_for_security
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import flask_wtf
from wtforms import TextField

from .models import User, db

class NoiModelView(ModelView):
    # The latest docs for flask-admin document a SecureForm class, but
    # this hasn't yet been added to the latest release, so we'll use
    # the "old" way of enabling CSRF support, documented here:
    #
    # http://flask-admin.readthedocs.org/en/v1.3.0/introduction/
    form_base_class = flask_wtf.Form

    can_delete = False
    can_create = False

    def is_accessible(self):
        return current_user.is_authenticated() and current_user.is_admin()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for_security('login', next=request.url))


class UserModelView(NoiModelView):
    column_list = ('first_name', 'last_name', 'email')
    form_columns = column_list
    column_searchable_list = ('first_name', 'last_name', 'email')

    def scaffold_form(self):
        form_class = super(UserModelView, self).scaffold_form()
        form_class.email = TextField('Email')
        return form_class

def init_app(app):
    admin = Admin(app, template_mode='bootstrap3')
    admin.add_view(UserModelView(User, db.session))
