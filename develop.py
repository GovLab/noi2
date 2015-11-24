"""
    This is a script to continuously re-run 'manage.py runserver' even
    when it throws an exception.

    Ordinarily this wouldn't really be needed, but because our app is running
    in Docker, we don't want to have to restart a bunch of containers
    just because there's a syntax error in one of our files.
"""

import os
import sys
import subprocess
import time

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
path = lambda *x: os.path.join(ROOT_DIR, *x)

def run_server():
    return subprocess.call([
        sys.executable,
        path('manage.py'),
        'runserver',
        '--host', '0.0.0.0'
    ])

def write(message):
    sys.stdout.write(message + '\n')
    sys.stdout.flush()

if __name__ == '__main__':
    while True:
        retval = run_server()
        write("Development server exited with code %d. " % retval)
        for i in [3, 2]:
            write("Restarting development server in %d seconds... " % i)
            time.sleep(1)
        write("Restarting development server in 1 second... ")
        time.sleep(1)
