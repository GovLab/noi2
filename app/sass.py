import subprocess

from sassutils.wsgi import SassMiddleware
import sassutils.builder

SASS_DIR = 'static/sass'
CSS_DIR = 'static/css'
PRIMARY_CSS_FILENAME = 'styles.scss.css'
BASE_POSTCSS_ARGS = ["postcss", "-u", "autoprefixer"]

class AutoprefixingMiddleware(object):
    def __init__(self, app, prefix):
        self.prefix = prefix
        self.app = app
        self._cache = {}

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '/')
        if path == self.prefix + '/' + PRIMARY_CSS_FILENAME:
            css = ''.join(chunk for chunk in self.app(environ, start_response))
            if css not in self._cache:
                popen = subprocess.Popen(
                    BASE_POSTCSS_ARGS,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdoutdata, stderrdata = popen.communicate(css)
                self._cache[css] = stdoutdata
            return self._cache[css]
        return self.app(environ, start_response)


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
        app.wsgi_app = AutoprefixingMiddleware(
            app.wsgi_app,
            app.jinja_env.globals['COMPILED_SASS_ROOT']
        )
    else:
        app.jinja_env.globals['COMPILED_SASS_ROOT'] = '/' + CSS_DIR

def build_files():
    sassutils.builder.build_directory('/noi/app/' + SASS_DIR,
                                      '/noi/app/' + CSS_DIR)
    subprocess.check_call(
        BASE_POSTCSS_ARGS +
        ["-r", '/noi/app/' + CSS_DIR + '/' + PRIMARY_CSS_FILENAME]
    )
