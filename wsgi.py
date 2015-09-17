'''
NoI wsgi

Create & run the app for gunicorn
'''

from app.factory import create_app

application = create_app()
