'''
NoI forms
'''

from app import DOMAINS, LOCALES
from app.models import User

from flask_wtf import Form
from flask_babel import lazy_gettext
from wtforms_alchemy import model_form_factory
from wtforms.fields import SelectMultipleField
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


class UserForm(ModelForm):  #pylint: disable=no-init,too-few-public-methods
    '''
    Form for users to edit their profile
    '''

    class Meta:  #pylint: disable=no-init,missing-docstring,old-style-class,too-few-public-methods
        model = User
        csrf = False
        exclude = ['password', 'active']

    languages = SelectMultipleField(label=lazy_gettext('Languages'),
                                    widget=ChosenSelect(multiple=True),
                                    choices=[(l.language, l.display_name) for l in LOCALES])
    expertise_domains = SelectMultipleField(label=lazy_gettext('Domains of Expertise'),
                                            widget=ChosenSelect(multiple=True),
                                            choices=[(v, v) for v in DOMAINS])
