#! /usr/bin/env python

import sys
import os
import pwd
import subprocess

HOST_UID = os.stat('/noi').st_uid
HOST_USER = os.environ.get('HOST_USER', 'code_executor_user')

def does_username_exist(username):
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False

def does_uid_exist(uid):
    try:
        pwd.getpwuid(uid)
        return True
    except KeyError:
        return False

if __name__ == '__main__':
    if HOST_UID != os.geteuid():
        if not does_uid_exist(HOST_UID):
            username = HOST_USER
            while does_username_exist(username):
                username += '0'
            home_dir = '/home/%s' % username
            #print "Creating username %s with UID %d" % (username, HOST_UID)
            subprocess.check_call([
                'useradd',
                '-d', home_dir,
                '-m', username,
                '-u', str(HOST_UID)
            ])
        os.environ['HOME'] = '/home/%s' % pwd.getpwuid(HOST_UID).pw_name
        os.setuid(HOST_UID)
    os.execvp(sys.argv[1], sys.argv[1:])
