'''
NoI Views

All views in the app, as a blueprint
'''

from flask import (Blueprint, render_template)

views = Blueprint('views', __name__)

@views.route('/')
def show(page):
    return render_template('base.html' % page)
