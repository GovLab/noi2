import os
import datetime
from flask import url_for

STATIC_LOGO_PATH = 'img/conferences'
FILESYSTEM_LOGO_PATH = '/noi/app/static/' + STATIC_LOGO_PATH

class Conferences(list):
    @property
    def featured(self):
        return [c for c in self if c.is_featured]

    @classmethod
    def from_yaml(cls, obj):
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

    @classmethod
    def from_yaml(cls, obj):
        if isinstance(obj['start_date'], basestring):
            obj['start_date'] = datetime.datetime.strptime(
                obj['start_date'],
                '%Y-%m-%d'
            ).date()
        return cls(**obj)

from_yaml = Conferences.from_yaml
