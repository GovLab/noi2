import os
import datetime
from flask import url_for

STATIC_LOGO_PATH = 'img/conferences'
FILESYSTEM_LOGO_PATH = '/noi/app/static/' + STATIC_LOGO_PATH

class Conference(object):
    def __init__(self, id, name, url, start_date, is_featured=False,
                 logo_filename=None):
        self.id = id
        self.name = name
        self.url = url
        self.start_date = start_date
        self.is_featured = is_featured
        self.logo_filename = logo_filename or None

        if logo_filename:
            abspath = os.path.join(FILESYSTEM_LOGO_PATH, logo_filename)
            if not os.path.exists(abspath):
                raise ValueError('Logo does not exist: %s' % abspath)

    @classmethod
    def from_yaml(cls, obj):
        obj['start_date'] = datetime.datetime.strptime(
            obj['start_date'],
            '%Y-%m-%d'
        ).date()
        return cls(**obj)
