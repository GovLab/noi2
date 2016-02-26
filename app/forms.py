'''
NoI forms
'''

from app import LOCALES, QUESTIONNAIRES, LEVELS, l10n
from app.models import User

from flask import current_app
from flask.ext.babel import get_locale
from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed
from flask_security.forms import (LoginForm, ConfirmRegisterForm,
                                  ForgotPasswordForm, ChangePasswordForm,
                                  ResetPasswordForm,
                                  SendConfirmationForm,
                                  email_required,
                                  email_validator, unique_user_email,
                                  valid_user_email,
                                  password_required, password_length, EqualTo)

from flask_babel import lazy_gettext
from wtforms_alchemy import model_form_factory, CountryField
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields import (SelectMultipleField, TextField, TextAreaField,
                            SelectField)
from wtforms.widgets import Select
from wtforms.validators import ValidationError, Required

import re


# The variable db here is a SQLAlchemy object instance from
# Flask-SQLAlchemy package
#from app.models import db

ModelForm = model_form_factory(Form)


class CallableChoicesSelectField(SelectField):
    '''
    Subclass of SelectField that can take a callable for `choices`.

    The function is only executed at instantiatino.
    '''
    def __init__(self, *args, **kwargs):
        if 'choices' in kwargs and hasattr(kwargs['choices'], '__call__'):
            kwargs['choices'] = kwargs['choices']()
        super(CallableChoicesSelectField, self).__init__(*args, **kwargs)


class CallableChoicesSelectMultipleField(SelectMultipleField):
    '''
    Subclass of SelectMultipleField that can take a callable for `choices`.

    The function is only executed at instantiatino.
    '''
    def __init__(self, *args, **kwargs):
        if 'choices' in kwargs and hasattr(kwargs['choices'], '__call__'):
            kwargs['choices'] = kwargs['choices']()
        super(CallableChoicesSelectMultipleField, self).__init__(*args, **kwargs)


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
        only = ['position', 'organization', 'country']

    @classmethod
    def is_not_empty(cls, user):
        '''
        Returns whether or not the user has filled out any of the
        fields in the form. Used to determine whether to skip past
        this form when resuming the registration process.
        '''

        for attr in cls.Meta.only:
            if getattr(user, attr):
                return True
        return False

    expertise_domain_names = CallableChoicesSelectMultipleField(
        label=lazy_gettext('Fields of Work'),
        widget=Select(multiple=True),
        choices=lambda: [(v, lazy_gettext(v)) for v in current_app.config['DOMAINS']])

image_validator = FileAllowed(
    ('jpg', 'jpeg', 'png'),
    lazy_gettext('Only jpeg, jpg, and png images are allowed.')
)

class PictureForm(Form):
    picture = FileField(validators=[image_validator])

class UserForm(ModelForm):  #pylint: disable=no-init,too-few-public-methods
    '''
    Form for users to edit their profile
    '''

    class Meta:  #pylint: disable=no-init,missing-docstring,old-style-class,too-few-public-methods
        model = User
        only = ['first_name', 'last_name', 'position', 'organization',
                'organization_type', 'city', 'country', 'projects']
        field_args = {
            'first_name': {
                'validators': [Required()]
            },
            'last_name': {
                'validators': [Required()]
            },
        }

    picture = FileField(
        label=lazy_gettext('User Picture'),
        description='Optional',
        validators=[image_validator]
    )

    locales = CallableChoicesSelectMultipleField(
        label=lazy_gettext('Languages'),
        widget=Select(multiple=True),
        choices=lambda: [(l.language, l.get_display_name())
                         for l in LOCALES])
    expertise_domain_names = CallableChoicesSelectMultipleField(
        label=lazy_gettext('Fields of Work'),
        widget=Select(multiple=True),
        choices=lambda: [(v, lazy_gettext(v)) for v in current_app.config['DOMAINS']])


class InviteForm(Form):
    '''
    Form for inviting a human to join the site.
    '''

    email = StringField(lazy_gettext('Email'),
                        validators=[email_required, email_validator])


class SharedMessageForm(Form):
    '''
    Form for submittin a message to share with the network.
    '''

    message = TextAreaField()


class SearchForm(Form):
    '''
    Form for searching the user database.
    '''

    questionnaire_area = CallableChoicesSelectField(
        choices=lambda: [
            ('ZZ', lazy_gettext('Choose an expertise area'))
        ] + [
            (q['id'], lazy_gettext(q['name']))
            for q in QUESTIONNAIRES
            if q['questions']
        ],
        default='ZZ'
    )
    country = CountryField()
    locale = CallableChoicesSelectField(
        choices=lambda: [
            ('ZZ', lazy_gettext('Choose a language'))
        ] + [
            (l.language, l.get_language_name(get_locale()))
             for l in LOCALES
        ],
        default='ZZ'
    )
    expertise_domain_name = CallableChoicesSelectField(
        choices=lambda: [
            ('ZZ', lazy_gettext('Choose a field of work'))
        ] + [
            (v, lazy_gettext(v)) for v in current_app.config['DOMAINS']
        ],
        default='ZZ'
    )

    # This doesn't actually appear as a field in a form, but as a tab
    # in a result set, so it's a bit unusual.
    skill_level = SelectField(
        choices=[(level['score'], '') for level in LEVELS.values()],
        coerce=int,
        default=LEVELS['LEVEL_I_CAN_DO_IT']['score']
    )

    fulltext = StringField()


class ChangeLocaleForm(Form):
    '''
    Form that allows the user to change the locale of the site.
    '''

    locale = SelectField(
        label=lazy_gettext('Language'),
        default=lambda: str(get_locale()),
        choices=[
            (str(l), l.get_display_name() or l.english_name or str(l))
            for l in l10n.VALID_LOCALES
        ]
    )


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
    email = StringField(lazy_gettext('Email'),
        validators=[email_required, email_validator, valid_user_email])


class NOILoginForm(LoginForm):
    '''
    Localizeable version of Flask-Security's LoginForm
    '''

    email = StringField(lazy_gettext('Email'))
    password = PasswordField(lazy_gettext('Password'))
    remember = BooleanField(lazy_gettext('Remember Me'))
    submit = SubmitField(lazy_gettext('Log in'))


class NOIConfirmRegisterForm(ConfirmRegisterForm):
    '''
    Localizeable version of Flask-Security's ConfirmRegisterForm
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


class NOIResetPasswordForm(ResetPasswordForm):
    '''
    Localizeable ResetPasswordForm
    '''

    submit = SubmitField(lazy_gettext('Reset Password'))
    password = PasswordField(
        lazy_gettext('Password'),
        validators=[password_required, password_length])
    password_confirm = PasswordField(
        lazy_gettext('Retype Password'),
        validators=[EqualTo('password', message='RETYPE_PASSWORD_MISMATCH')])


class NOIChangePasswordForm(ChangePasswordForm):
    '''
    Localizeable ChangePasswordForm
    '''

    password = PasswordField(lazy_gettext('Password'),
                             validators=[password_required])

    new_password = PasswordField(
        lazy_gettext('New Password'),
        validators=[password_required, password_length])

    new_password_confirm = PasswordField(
        lazy_gettext('Retype Password'),
        validators=[EqualTo('new_password', message='RETYPE_PASSWORD_MISMATCH')])

    submit = SubmitField(lazy_gettext('Change Password'))
