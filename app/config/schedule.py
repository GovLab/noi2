'''
NoI schedule

Schedule for async tasks
'''

from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'backup': {
        'task': 'app.tasks.backup',
        'schedule': timedelta(hours=24)
    }
}
