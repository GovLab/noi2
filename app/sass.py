from sassutils.wsgi import SassMiddleware
import sassutils.builder

SASS_DIR = 'static/sass'
CSS_DIR = 'static/css'

def init_app(app):
    if app.config['DEBUG']:
        # If we're debugging, we want to build SASS for each
        # request so that we have a nice development flow:
        #
        # http://hongminhee.org/libsass-python/frameworks/flask.html
        #
        # However, because nginx intercepts everything at /static/, we can't
        # have the SASS middleware use that path, so instead we'll
        # put all compiled SASS in a different path that we have
        # control over.
        app.jinja_env.globals['COMPILED_SASS_ROOT'] = '/sass-middleware'
        app.wsgi_app = SassMiddleware(app.wsgi_app, {
            'app': (SASS_DIR, CSS_DIR,
                    app.jinja_env.globals['COMPILED_SASS_ROOT'])
        })
    else:
        app.jinja_env.globals['COMPILED_SASS_ROOT'] = '/' + CSS_DIR

def build_files():
    sassutils.builder.build_directory('/noi/app/' + SASS_DIR,
                                      '/noi/app/' + CSS_DIR)
