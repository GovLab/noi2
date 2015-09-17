'''
NoI tasks

Asynchronous tasks
'''

from app import celery

from flask_alchemydumps import create, autoclean
#from flask.ext.security import confirmable


@celery.task()
def backup():
    '''
    Backup the db
    '''
    create()
    autoclean()


#@celery.task()
#def send_email_confirmation(user):
#    confirmable.send_confirmation_instructions(user)
