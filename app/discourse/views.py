from flask import Blueprint
from flask_login import login_required, current_user

views = Blueprint('discourse', __name__)

@views.route('/discourse/sso')
@login_required
def sso():
    raise NotImplementedError()
