'''
NoI forms
'''

from app import LOCALES
from app.models import User

from flask import current_app
from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed
from flask_security.forms import (LoginForm, RegisterForm, ConfirmRegisterForm,
                                  ForgotPasswordForm, ChangePasswordForm,
                                  ResetPasswordForm,
                                  SendConfirmationForm, email_required,
                                  email_validator, unique_user_email,
                                  password_required, password_length, EqualTo)

from flask_babel import lazy_gettext
from wtforms_alchemy import model_form_factory, CountryField
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields import SelectMultipleField, TextField, TextAreaField
from wtforms.widgets import Select
from wtforms.validators import ValidationError, Required

import re


# The variable db here is a SQLAlchemy object instance from
# Flask-SQLAlchemy package
#from app.models import db

ModelForm = model_form_factory(Form)


class CallableChoicesSelectMultipleField(SelectMultipleField):
    '''
    Subclass of SelectMultipleField that can take a callable for `choices`.

    The function is only executed at instantiatino.
    '''
    def __init__(self, *args, **kwargs):
        if 'choices' in kwargs and hasattr(kwargs['choices'], '__call__'):
            kwargs['choices'] = kwargs['choices']()
        super(CallableChoicesSelectMultipleField, self).__init__(*args, **kwargs)


class ChosenSelect(Select):  #pylint: disable=no-init,too-few-public-methods
    '''
    Customization of Select widget to use chosen
    '''
    def __call__(self, field, **kwargs):
        #if field.errors:
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'%s form-select chosen-select' % (c)
        kwargs['data-placeholder'] = kwargs.pop('placeholder')
        return super(ChosenSelect, self).__call__(field, **kwargs)


# Monkey-patch CountryField to have ability to not select a country.
CountryField._get_choices_old = CountryField._get_choices
def _get_choices(self):
    '''
    Customization of Country field to allow selection of `None`.
    '''
    choices = self._get_choices_old()
    choices.insert(0, ('ZZ', lazy_gettext('Choose your country'),))
    return choices
CountryField._get_choices = _get_choices

class RegisterStep2Form(ModelForm):
    class Meta:  #pylint: disable=no-init,missing-docstring,old-style-class,too-few-public-methods
        model = User
        only = ['position', 'organization', 'organization_type', 'city',
                'country']

class UserForm(ModelForm):  #pylint: disable=no-init,too-few-public-methods
    '''
    Form for users to edit their profile
    '''

    class Meta:  #pylint: disable=no-init,missing-docstring,old-style-class,too-few-public-methods
        model = User
        only = ['first_name', 'last_name', 'position', 'organization',
                'organization_type', 'city', 'country', 'projects',
                'has_picture']

    picture = FileField(
        label=lazy_gettext('User Picture'),
        description='Optional',
        validators=[FileAllowed(
            ('jpg', 'jpeg', 'png'),
            lazy_gettext('Only jpeg, jpg, and png images are allowed.'))]
    )

    locales = CallableChoicesSelectMultipleField(
        label=lazy_gettext('Languages'),
        widget=ChosenSelect(multiple=True),
        choices=lambda: [(l.language, l.get_language_name(current_app.config.get(
            'BABEL_DEFAULT_LOCALE'))) for l in LOCALES])
    expertise_domain_names = CallableChoicesSelectMultipleField(
        label=lazy_gettext('Domains of Expertise'),
        widget=ChosenSelect(multiple=True),
        choices=lambda: [(v, lazy_gettext(v)) for v in current_app.config['DOMAINS']])


class SharedMessageForm(Form):
    '''
    Form for submittin a message to share with the network.
    '''

    message = TextAreaField(
        label=lazy_gettext('Have a question or something to share about innovation?')
    )


class SearchForm(Form):
    '''
    Form for searching the user database.
    '''
    country = CountryField()
    locales = CallableChoicesSelectMultipleField(
        label=lazy_gettext('Languages'),
        widget=ChosenSelect(multiple=True),
        choices=lambda: [(l.language, l.get_language_name(current_app.config.get(
            'BABEL_DEFAULT_LOCALE'))) for l in LOCALES])
    expertise_domain_names = CallableChoicesSelectMultipleField(
        label=lazy_gettext('Domains of Expertise'),
        widget=ChosenSelect(multiple=True),
        choices=lambda: [(v, lazy_gettext(v)) for v in current_app.config['DOMAINS']])
    fulltext = TextField()


class NOISendConfirmationForm(SendConfirmationForm):
    '''
    Localizeable version of Flask-Security's SendConfirmationForm
    '''
    submit = SubmitField(lazy_gettext('Resend Confirmation Instructions'))


class NOIForgotPasswordForm(ForgotPasswordForm):
    '''
    Localizeable version of Flask-Security's ForgotPasswordForm
    '''
    submit = SubmitField(lazy_gettext('Recover Password'))


class NOILoginForm(LoginForm):
    '''
    Localizeable version of Flask-Security's LoginForm
    '''

    email = StringField(lazy_gettext('Email'))
    password = PasswordField(lazy_gettext('Password'))
    remember = BooleanField(lazy_gettext('Remember Me'))
    submit = SubmitField(lazy_gettext('Log in'))


class NOIRegisterForm(RegisterForm):
    '''
    Localizeable version of Flask-Security's RegisterForm
    '''

    # Note that extra fields in this registration form are passed
    # directly on to the User model as kwargs, so the names need
    # to match exactly. For more information, see:
    #
    # https://pythonhosted.org/Flask-Security/customizing.html
    first_name = StringField(lazy_gettext('First Name'),
                             validators=[Required()])
    last_name = StringField(lazy_gettext('Last Name'),
                            validators=[Required()])

    email = StringField(
        lazy_gettext('Email'),
        validators=[email_required, email_validator, unique_user_email])
    password = PasswordField(
        lazy_gettext('Password'), validators=[password_required,
                                              password_length])
    submit = SubmitField(lazy_gettext('Sign up'))


class NOIConfirmRegisterForm(ConfirmRegisterForm):
    '''
    Custom registration form that limits emails to a certain domain.
    '''

    def validate_email(self, field):
        '''
        Validate email is OK for this domain
        '''
        value = field.data
        email_regex = current_app.config.get('EMAIL_REGEX')
        if email_regex:
            if re.match(email_regex, value):
                return value

        email_whitelist = current_app.config.get('EMAIL_WHITELIST')
        if email_whitelist:
            if value in email_whitelist:
                return value

        if email_regex:
            raise ValidationError(lazy_gettext(
                '%(value)s is not a valid email address: %(explanation)s' %
                {'value': value,
                 'explanation': lazy_gettext(current_app.config.get('EMAIL_EXPLANATION'))}
            ))


class NOIResetPasswordForm(ResetPasswordForm):
    '''
    Localizeable ResetPasswordForm
    '''

    submit = SubmitField(lazy_gettext('Reset Password'))


class NOIChangePasswordForm(ChangePasswordForm):
    '''
    Localizeable ChangePasswordForm
    '''

    new_password = PasswordField(
        lazy_gettext('New Password'),
        validators=[password_required, password_length])

    new_password_confirm = PasswordField(
        lazy_gettext('Retype Password'),
        validators=[EqualTo('new_password', message='RETYPE_PASSWORD_MISMATCH')])

    submit = SubmitField(lazy_gettext('Change Password'))
