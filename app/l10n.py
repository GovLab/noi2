from flask import request

DEFAULT_LANGUAGE = 'en'

TRANSLATIONS = ['es_MX']

def init_app(app):
    babel = app.extensions['babel']

    @babel.localeselector
    def get_locale():
        return request.accept_languages.best_match(
            [DEFAULT_LANGUAGE] +
            TRANSLATIONS
        )
