from werkzeug.local import LocalProxy
from flask import current_app

class DiscourseConfig(object):
    def __init__(self, config):
        self.api_key = config['api_key']
        self.origin = config['origin']
        self.sso_secret = config['sso_secret']
        self.admin_username = 'system'

    def url(self, path):
        return self.origin + path

    @classmethod
    def from_current_app(cls):
        return cls(current_app.config['DISCOURSE'])

config = LocalProxy(DiscourseConfig.from_current_app)
