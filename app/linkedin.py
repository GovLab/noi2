from flask import Blueprint, flash, redirect, url_for, session
from flask_babel import gettext
from werkzeug.security import gen_salt

from app import oauth

from flask import current_app, request

linkedin = oauth.remote_app(
    'linkedin',
    app_key='LINKEDIN',
    request_token_url=None,
    request_token_params={
        'scope': 'r_basicprofile',
        'state': lambda: session['linkedin_state']
    },
    base_url='https://api.linkedin.com/',
    authorize_url='https://www.linkedin.com/uas/oauth2/authorization',
    access_token_method='POST',
    access_token_url='https://www.linkedin.com/uas/oauth2/accessToken',
)

views = Blueprint('linkedin', __name__)

@views.route('/linkedin/authorize')
def authorize():
    session['linkedin_state'] = gen_salt(10)
    return linkedin.authorize(
        callback=url_for('linkedin.callback', _external=True)
    )

@views.route('/linkedin/callback')
def callback():
    state = request.args.get('state')
    if not state or session.get('linkedin_state') != state:
        return 'Invalid state'
    del session['linkedin_state']

    resp = linkedin.authorized_response()
    if resp is None:
        flash(gettext(u'Connection with LinkedIn canceled.'), 'error')
    else:
        flash(gettext(u'Connection to LinkedIn established.'))
    return redirect(url_for('views.my_profile'))
