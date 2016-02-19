from flask import Blueprint, request, redirect, abort
from flask_login import login_required, current_user

from . import sso
from .config import config

views = Blueprint('discourse', __name__)

# TODO: For some reason this does NOT work when the login_required
# decorator redirects the user to sign in first; the SSO payload is
# somehow being corrupted through the redirects, and by the time the
# user's browser gets back to this endpoint, the signature is invalid.

@views.route('/discourse/sso')
@login_required
def sso_endpoint():
    # TODO: If the current user doesn't have a username, they can't
    # actually log into Discourse yet. We may want to prompt them to
    # create a username before continuing into discourse, or we could
    # just deny the request, but we ought to do something.

    # TODO: Ensure that the user's email address is validated, or
    # else our discourse installation will be "extremely vulnerable".

    try:
        nonce = sso.unpack_and_verify_payload(request.args)['nonce']
    except sso.InvalidSignatureError:
        return abort(400)

    qs = sso.user_info_qs(current_user, nonce)

    return redirect(config.url('/session/sso_login') + '?' + qs)
