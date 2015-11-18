from app import csp
from flask import (Blueprint, render_template, current_app,
                   send_from_directory, abort)
from jinja2 import TemplateNotFound

import os
import re

views = Blueprint('style_guide', __name__)  # pylint: disable=invalid-name

def get_pages():
    filenames = os.listdir('/noi/app/templates/style-guide')
    pages = []
    for filename in filenames:
        match = re.search('^([A-Za-z0-9\-_]+)\.html$', filename)
        if match:
            pages.append(match.group(1))
    return pages

@views.route('/style-guide/')
@csp.script_src(["'unsafe-inline'"])
def home():
    '''
    Root page for the NOI Style Guide.
    '''

    return render_template('style-guide/index.html', pages=get_pages())

@views.route('/style-guide/<pageid>')
@csp.script_src(["'unsafe-inline'"])
def page(pageid):
    '''
    Renders an individual template page for the NOI Style Guide.
    '''

    if not re.search(r'^[A-Za-z0-9\-_]+$', pageid):
        abort(404)
    try:
        return render_template('style-guide/%s.html' % pageid)
    except TemplateNotFound:
        abort(404)

@views.route('/style-guide/static/<path:path>')
def send_static_asset(path):
    '''
    Delivers a static asset for the NOI Style Guide.
    '''

    return send_from_directory('/noi/app/templates/style-guide/static',
                               path)
