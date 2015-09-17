'''
NoI forms
'''

from app import LOCALES
from app.models import User

from flask import current_app
from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed
from flask_security.forms import ConfirmRegisterForm

from flask_babel import lazy_gettext
from wtforms_alchemy import model_form_factory, CountryField
from wtforms.fields import SelectMultipleField, TextField
from wtforms.widgets import Select
from wtforms.validators import ValidationError

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


class UserForm(ModelForm):  #pylint: disable=no-init,too-few-public-methods
    '''
    Form for users to edit their profile
    '''

    class Meta:  #pylint: disable=no-init,missing-docstring,old-style-class,too-few-public-methods
        model = User
        exclude = ['password', 'active', 'email', 'picture_id', 'deployment']

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


class EmailRestrictRegisterForm(ConfirmRegisterForm):
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
