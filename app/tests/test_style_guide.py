from app import style_guide
from app import assets, csrf
from app.views import views

from flask import Flask
from flask.ext.testing import TestCase

class StyleGuideTests(TestCase):
    def create_app(self):
        app = Flask('app')
        app.config['SECRET_KEY'] = 'test'
        app.register_blueprint(views)
        app.register_blueprint(style_guide.views)
        assets.init_app(app)
        csrf.init_app(app)
        return app

    def test_index_is_ok(self):
        self.assert200(self.client.get('/style-guide/'))

    def test_static_assets_are_ok(self):
        self.assert200(self.client.get('/style-guide/static/img/mobile-ui-blur.jpg'))

    def test_nonexistent_pages_are_not_found(self):
        self.assert404(self.client.get('/style-guide/blarg'))
        self.assert404(self.client.get('/style-guide/#%@#$#!'))

    def test_pages_are_ok(self):
        for pageid in style_guide.get_pages():
            self.assert200(self.client.get('/style-guide/%s' % pageid))
