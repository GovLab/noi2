'''
NoI celery

launch celery
'''

from app.factory import create_celery

celery = create_celery()
