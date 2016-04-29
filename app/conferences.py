import os
import datetime
from flask import url_for, current_app
import six
from sqlalchemy import types

STATIC_LOGO_PATH = 'img/conferences'
FILESYSTEM_LOGO_PATH = '/noi/app/static/' + STATIC_LOGO_PATH

class ConferenceType(types.TypeDecorator):
    '''
    SQLAlchemy type decorator that stores the id of a conference in
    the database, but converts it to a Conference object upon
    retrieval.
    '''

    impl = types.Unicode(50)

    def process_bind_param(self, value, dialect):
        if isinstance(value, Conference):
            return six.text_type(value.id)

        if isinstance(value, six.string_types):
            return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return current_app.config['CONFERENCES'].from_id(value)

class Conferences(list):
    def choices(self):
        '''
        Get available choices for use in e.g. a <select> form field.
        '''

        return [(c.id, c.name) for c in self]

    def from_id(self, id):
        '''
        Return the Conference with the given id.
        '''

        ids = [c for c in self if c.id == id]
        if len(ids) != 1:
            raise ValueError('Conference w/ unique id %s not found' % id)
        return ids[0]

    @property
    def featured(self):
        '''
        Return only the conferences which are featured.
        '''

        return self.__class__([c for c in self if c.is_featured])

    @classmethod
    def from_yaml(cls, obj):
        '''
        Convert a list from YAML into a Conferences object.
        '''

        return cls(map(Conference.from_yaml, obj))

class Conference(object):
    def __init__(self, id, name, url, start_date, is_featured=False,
                 logo_filename=None):
        self.id = id
        self.name = name
        self.url = url
        self.start_date = start_date
        self.is_featured = is_featured
        self.logo_filename = logo_filename or None

        if not isinstance(start_date, datetime.date):
            raise ValueError('start_date must be a datetime.date')

        if not isinstance(is_featured, bool):
            raise ValueError('is_featured must be a boolean')

        if logo_filename:
            abspath = os.path.join(FILESYSTEM_LOGO_PATH, logo_filename)
            if not os.path.exists(abspath):
                raise ValueError('Logo does not exist: %s' % abspath)

    @property
    def logo_url(self):
        if self.logo_filename:
            return url_for('static', filename=self.logo_filename)
        return 'http://placehold.it/32x32'

    @classmethod
    def from_yaml(cls, obj):
        if isinstance(obj['start_date'], basestring):
            obj['start_date'] = datetime.datetime.strptime(
                obj['start_date'],
                '%Y-%m-%d'
            ).date()
        return cls(**obj)

from_yaml = Conferences.from_yaml
