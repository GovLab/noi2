import datetime

from flask import Blueprint, flash, redirect, url_for, session
from flask_login import login_required, current_user
from flask_babel import gettext
from flask_oauthlib.client import OAuthException
from werkzeug.security import gen_salt
from sqlalchemy_utils import Country

from app import oauth
from app.models import db, UserLinkedinInfo

from flask import current_app, request

# Minimum amount of time, in seconds, that we think a token has to live.
# Because the LinkedIn server gives us an `expires_in` based on the time
# *they* sent their response, we should account for the amount of time it took
# for the response to get back to us. We should also account for the
# amount of time it might take for our OAuth2 request to reach their
# server.
MIN_TOKEN_LIFETIME = 120

# These are the user info fields to retrieve for users from LinkedIn.
# For more information, see:
#
#     https://developer.linkedin.com/docs/fields/basic-profile
#
USER_INFO_FIELDS = [
    'id',
    'first-name',
    'last-name',
    'maiden-name',
    'formatted-name',
    'phonetic-first-name',
    'phonetic-last-name',
    'formatted-phonetic-name',
    'headline',
    'location',
    'industry',
    'current-share',
    'num-connections',
    'num-connections-capped',
    'summary',
    'specialties',
    'positions',
    'picture-url',
    'picture-urls::(original)',
    'site-standard-profile-request',
    'api-standard-profile-request',
    'public-profile-url',
]

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

def retrieve_access_token(user):
    if user.linkedin is not None:
        if user.linkedin.expires_in.total_seconds() > MIN_TOKEN_LIFETIME:
            return (user.linkedin.access_token, '')

def store_access_token(user, resp):
    expiry = datetime.datetime.now() + datetime.timedelta(
        seconds=resp['expires_in']
    )

    if user.linkedin is None:
        user.linkedin = UserLinkedinInfo()
    user.linkedin.access_token = resp['access_token']
    user.linkedin.access_token_expiry = expiry
    db.session.add(user)
    db.session.commit()

def get_user_info(user):
    # https://developer-programs.linkedin.com/documents/field-selectors
    url = 'v1/people/~:(%s)?format=json' % ','.join(USER_INFO_FIELDS)
    token = retrieve_access_token(user)

    if token is None:
        raise OAuthException(
            'Access token unavailable or expired for %s' % user.email
        )

    res = linkedin.get(url, token=token)

    if res.status != 200:
        raise OAuthException('Server returned HTTP %d: %s' % (
            res.status,
            repr(res.data)
        ), data=res.data)

    return res.data

def update_user_fields_from_profile(user, info):
    location = info.get('location')
    if location:
        if 'name' in location and not user.city:
            user.city = location['name']
        if 'country' in location and 'code' in location['country']:
            country_code = location['country']['code'].upper()
            try:
                user.country = Country(country_code)
            except ValueError:
                pass

    positions = info.get('positions')
    if positions and len(positions.get('values', [])) >= 1:
        position = positions['values'][0]
        org = position.get('company') and position['company'].get('name')
        if org and not user.organization:
            user.organization = org
        if position.get('title') and not user.position:
            user.position = position['title']

    if info.get('headline') and not user.position:
        user.position = info['headline']

def update_user_info(user):
    info = get_user_info(user)
    user.linkedin.user_info = info
    update_user_fields_from_profile(user, info)
    db.session.commit()

@views.route('/linkedin/deauthorize')
@login_required
def deauthorize():
    if current_user.linkedin:
        db.session.delete(current_user.linkedin)
        db.session.commit()
    flash(gettext(u'Disconnected from LinkedIn.'))
    return redirect(url_for('views.my_profile'))

@views.route('/linkedin/authorize')
@login_required
def authorize():
    session['linkedin_state'] = gen_salt(10)
    return linkedin.authorize(
        callback=url_for('linkedin.callback', _external=True)
    )

@views.route('/linkedin/callback')
@login_required
def callback():
    state = request.args.get('state')
    if not state or session.get('linkedin_state') != state:
        return 'Invalid state'
    del session['linkedin_state']

    resp = linkedin.authorized_response()
    if resp is None:
        flash(gettext(u'Connection with LinkedIn canceled.'), 'error')
    else:
        store_access_token(current_user, resp)
        update_user_info(current_user)
        flash(gettext(u'Connection to LinkedIn established.'))
    return redirect(url_for('views.my_profile'))
