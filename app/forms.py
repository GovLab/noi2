'''
NoI forms
'''

from app import DOMAINS, LOCALES
from app.models import User

from flask_wtf import Form
from flask_babel import lazy_gettext
from wtforms_alchemy import model_form_factory, CountryField
from wtforms.fields import SelectMultipleField, TextField
from wtforms.widgets import Select


# The variable db here is a SQLAlchemy object instance from
# Flask-SQLAlchemy package
#from app.models import db

ModelForm = model_form_factory(Form)


class ChosenSelect(Select):  #pylint: disable=no-init,too-few-public-methods
    '''
    Customization of Select widget to use chosen
    '''
    def __call__(self, field, **kwargs):
        #if field.errors:
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'%s form-select chosen-select' % (c)
        return super(ChosenSelect, self).__call__(field, **kwargs)


# Monkey-patch CountryField to have ability to not select a country.
CountryField._get_choices_old = CountryField._get_choices
def _get_choices(self):
    '''
    Customization of Country field to allow selection of `None`.
    '''
    choices = self._get_choices_old()
    choices.insert(0, ('ZZ', '',))
    return choices
CountryField._get_choices = _get_choices


class UserForm(ModelForm):  #pylint: disable=no-init,too-few-public-methods
    '''
    Form for users to edit their profile
    '''

    class Meta:  #pylint: disable=no-init,missing-docstring,old-style-class,too-few-public-methods
        model = User
        exclude = ['password', 'active']

    locales = SelectMultipleField(label=lazy_gettext('Languages'),
                                  widget=ChosenSelect(multiple=True),
                                  choices=[(l.language, l.display_name) for l in LOCALES])
    expertise_domain_names = SelectMultipleField(label=lazy_gettext('Domains of Expertise'),
                                                 widget=ChosenSelect(multiple=True),
                                                 choices=[(v, v) for v in DOMAINS])


class SearchForm(Form):
    '''
    Form for searching the user database.
    '''
    country = CountryField()
    locales = SelectMultipleField(label=lazy_gettext('Languages'),
                                  widget=ChosenSelect(multiple=True),
                                  choices=[(l.language, l.display_name) for l in LOCALES])
    expertise_domain_names = SelectMultipleField(label=lazy_gettext('Domains of Expertise'),
                                                 widget=ChosenSelect(multiple=True),
                                                 choices=[(v, v) for v in DOMAINS])
    fulltext = TextField()
