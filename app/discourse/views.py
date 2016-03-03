from flask import Blueprint, request, redirect, abort
from flask_login import current_user

from .. import csrf
from ..views import full_registration_required
from . import sso, models
from .config import config

views = Blueprint('discourse', __name__)

@views.route('/discourse/webhook/<event_name>', methods=['POST'])
@csrf.exempt
def webhook(event_name):
    # TODO: Consider checking the payload to ensure the API key is
    # valid.
    models.DiscourseTopicEvent.update()
    return "Thanks!"

@views.route('/discourse/sso')
@full_registration_required
def sso_endpoint():
    try:
        nonce = sso.unpack_and_verify_payload(request.args)['nonce']
    except sso.InvalidSignatureError:
        return abort(400)

    if not current_user.username:
        current_user.autogenerate_and_commit_username()

    qs = sso.user_info_qs(current_user, nonce)

    return redirect(config.url('/session/sso_login') + '?' + qs)
