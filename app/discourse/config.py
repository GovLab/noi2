from werkzeug.local import LocalProxy
from flask import current_app

class DiscourseConfig(object):
    def __init__(self, api_key, origin):
        self.api_key = api_key
        self.origin = origin

    def url(self, path):
        return self.origin + path

    @classmethod
    def from_current_app(cls):
        return cls(**current_app.config['DISCOURSE'])

config = LocalProxy(DiscourseConfig.from_current_app)
