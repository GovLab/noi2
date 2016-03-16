import flask
from flask import Blueprint, render_template

blueprint = flask.Blueprint('error_handlers', __name__)

@blueprint.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
