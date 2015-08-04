'''
NoI __init__

Creates globals
'''

from flask.ext.assets import Bundle, Environment
from flask.ext.security import Security
from flask.ext.cache import Cache
from flask.ext.bcrypt import Bcrypt
from flask.ext.uploads import UploadSet, IMAGES
from celery import Celery
from flask_mail import Mail
from flask_s3 import FlaskS3
from flask_wtf.csrf import CsrfProtect

s3 = FlaskS3()
mail = Mail()
security = Security()
csrf = CsrfProtect()
bcrypt = Bcrypt()

celery = Celery(
    __name__,
    #broker=os.environ.get('REDISGREEN_URL', None),
    include=[]
)

assets = Environment()

main_css = Bundle('css/vendor/bootstrap.css',
                  output='gen/main_packed.%(version)s.css')
assets.register('main_css', main_css)

main_js = Bundle('js/plugins.js',
                 #filters='jsmin',
                 output='gen/main_packed.%(version)s.js')
assets.register('main_js', main_js)

photos = UploadSet('photos', IMAGES)

cache = Cache()
