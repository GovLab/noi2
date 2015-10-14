from flask import request

import os

TRANSLATIONS = ['en'] + os.listdir('/noi/app/translations')

def init_app(app):
    babel = app.extensions['babel']

    @babel.localeselector
    def get_locale():
        return request.accept_languages.best_match(TRANSLATIONS)
