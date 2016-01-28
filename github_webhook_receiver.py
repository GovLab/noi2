'''
    This script can be used to run 'docker-compose up' along with a
    webserver that waits for a GitHub webhook. When a webhook
    is triggered, docker-compose gracefully shuts down, 'git pull' is
    called, and docker-compose is started up again.

    Assuming this script was started with its default options, 
    you can run the following to test it manually:

        curl -H "Content-Type: application/json" \\
             -d '{"zen":"Design for failure."}' http://localhost:8320
'''

# This script requires Python 2.7 and has no other dependencies.

import os
import sys
import json
import hmac
import hashlib
import argparse
import httplib
import threading
import subprocess
import signal
import textwrap
from functools import partial
from wsgiref.simple_server import make_server

import unittest
import StringIO

DEFAULT_PORT = 8320

MAX_CONTENT_LENGTH = 5 * 1024 * 1024

MY_DIR = os.path.abspath(os.path.dirname(__file__))

path = lambda *x: os.path.join(MY_DIR, *x)

# These globals are used for inter-thread communication.
docker_compose = None
webhook_activated = False

def get_current_git_head():
    '''
    Returns the current git HEAD, e.g. 'refs/heads/master'.
    '''

    with open(path('.git', 'HEAD')) as f:
        return f.read().split()[1].strip()

def process_payload(payload):
    '''
    Process the parsed payload of a GitHub webhook.
    '''

    global webhook_activated

    if (payload.get('zen') != 'Design for failure.' and \
        payload.get('ref') != get_current_git_head()):
        return "Thanks, but no thanks."
    if docker_compose is None or webhook_activated:
        return "Thanks, but I can't do anything with that right now."
    webhook_activated = True
    docker_compose.send_signal(signal.SIGINT)

def app(env, start_response, secret=None, process_payload=process_payload):
    '''
    WSGI app to process GitHub webhooks.
    '''

    def abort(msg, status_code=httplib.BAD_REQUEST):
        status = '%d %s' % (status_code, httplib.responses[status_code])
        response_headers = [('Content-Type', 'text/plain')]
        start_response(status, response_headers)
        return [msg]

    if env['REQUEST_METHOD'] != 'POST':
        return abort('must be POST', httplib.METHOD_NOT_ALLOWED)
    if env.get('CONTENT_TYPE') != 'application/json':
        return abort('must be json')
    try:
        content_length = int(env.get('CONTENT_LENGTH', ''))
        if content_length <= 0:
            raise ValueError()
    except ValueError:
        return abort('invalid content length', httplib.LENGTH_REQUIRED)
    if content_length > MAX_CONTENT_LENGTH:
        return abort('content length too big',
                     httplib.REQUEST_ENTITY_TOO_LARGE)

    content = env['wsgi.input'].read(content_length)

    try:
        payload = json.loads(content)
    except ValueError:
        return abort('invalid JSON payload')

    if secret is not None:
        # https://developer.github.com/webhooks/securing/

        try:
            alg, expected_digest = env.get('HTTP_X_HUB_SIGNATURE').split('=')
        except:
            return abort('malformed signature')

        if alg not in hashlib.algorithms:
            return abort('invalid or unsupported hash algorithm')
        hmacsign = hmac.new(secret, content, getattr(hashlib, alg))
        if hmacsign.hexdigest() != expected_digest:
            return abort('invalid signature digest')

    response = process_payload(payload)
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [response or 'Thanks!']

def run_httpd(args):
    '''
    Run the web server that accepts GitHub webhooks.
    '''

    httpd = make_server(
        args.ip,
        args.port,
        partial(app, secret=args.secret)
    )

    print "waiting on port %d for webhook w/ secret %s" % (
        args.port,
        repr(args.secret)
    )

    httpd.serve_forever()

def run_docker_compose():
    '''
    Run 'docker-compose up' until it exits.
    '''

    global docker_compose

    docker_compose = subprocess.Popen(['docker-compose', 'up'])
    returncode = docker_compose.wait()
    docker_compose = None

    return returncode

def run_everything(args):
    '''
    Run the web server and docker-compose simultaneously, and
    orchestrate between the two.
    '''

    global webhook_activated

    httpd_thread = threading.Thread(target=run_httpd, kwargs=dict(
        args=args
    ))
    httpd_thread.daemon = True
    httpd_thread.start()

    # Ignore Ctrl-C, we'll instead have docker-compose handle it.
    signal.signal(signal.SIGINT, lambda signal, frame: None)

    while True:
        returncode = run_docker_compose()
        if webhook_activated:
            subprocess.check_call(['git', 'pull'])
            webhook_activated = False
        else:
            print "Webhook not activated, exiting with code %d." % returncode
            sys.exit(returncode)

def main():
    '''
    Primary entrypoint for the script.
    '''

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__)
    )
    parser.add_argument(
        '--secret', help='set secret for GitHub webhook'
    )
    parser.add_argument(
        '--ip', default='',
        help='IP address to listen on for webhook (default is all IPs)'
    )
    parser.add_argument(
        '--port', default=DEFAULT_PORT, type=int,
        help='Port to listen on for webhook (default is %d)' % DEFAULT_PORT
    )
    parser.add_argument(
        '--test', action='store_true', help='run test suite and exit'
    )
    parser.add_argument(
        '--without-docker', action='store_true',
        help='do not run docker-compose (useful for testing)'
    )
    args = parser.parse_args()

    if args.test:
        return unittest.main(argv=sys.argv[:1] + ['-v'])

    if args.without_docker:
        return run_httpd(args)

    run_everything(args)

class AppTests(unittest.TestCase):
    '''
    Test suite for the WSGI app.
    '''

    DEFAULT_ENV = dict(
        REQUEST_METHOD='POST',
        CONTENT_TYPE='application/json',
    )

    class FakeResponse(object):
        def __init__(self, env, app):
            if not 'wsgi.input' in env:
                env['wsgi.input'] = StringIO.StringIO()
            self.body = ''.join(app(env, self.start_response))

        def start_response(self, status, response_headers):
            self.headers = dict(response_headers)
            self.status = status
            self.status_code = int(status.split(' ')[0])

    def setUp(self):
        self.app = partial(app, process_payload=self.fake_process_payload)
        self.secret = None
        self.process_payload_arg = None
        self.response = None
        self.env = self.DEFAULT_ENV.copy()

    def fake_process_payload(self, payload):
        self.process_payload_arg = payload

    def set_secret(self, secret):
        if self.secret is not None: raise AssertionError()
        self.secret = secret
        self.app = partial(self.app, secret=secret)

    def set_payload(self, payload):
        self.env['wsgi.input'] = StringIO.StringIO(payload)
        self.env['CONTENT_LENGTH'] = len(payload)

    def set_json_payload(self, payload):
        self.set_payload(json.dumps(payload))

    def set_signed_json_payload(self, payload):
        if self.secret is None:
            self.set_secret('foo')
        raw_payload = json.dumps(payload)
        self.set_payload(raw_payload)
        self.set_signature('sha1=%s' % hmac.new(
            self.secret,
            raw_payload,
            hashlib.sha1
        ).hexdigest())

    def set_signature(self, signature):
        self.env['HTTP_X_HUB_SIGNATURE'] = signature

    def request(self):
        self.response = self.FakeResponse(self.env, self.app)

    def test_get_is_rejected(self):
        self.env['REQUEST_METHOD'] = 'GET'
        self.request()
        self.assertEqual(self.response.status_code, 405)
        self.assertEqual(self.response.body, 'must be POST')

    def test_text_is_rejected(self):
        self.env['CONTENT_TYPE'] = 'text/plain'
        self.request()
        self.assertEqual(self.response.status_code, 400)
        self.assertEqual(self.response.body, 'must be json')

    def test_unspecified_length_is_rejected(self):
        self.request()
        self.assertEqual(self.response.status_code, 411)
        self.assertEqual(self.response.body, 'invalid content length')

    def test_low_length_is_rejected(self):
        for length in ['-5', '0']:
            self.env['CONTENT_LENGTH'] = length
            self.request()
            self.assertEqual(self.response.status_code, 411)
            self.assertEqual(self.response.body, 'invalid content length')

    def test_high_length_is_rejected(self):
        self.env['CONTENT_LENGTH'] = '9999999999999'
        self.request()
        self.assertEqual(self.response.status_code, 413)
        self.assertEqual(self.response.body, 'content length too big')

    def test_no_payload_is_rejected(self):
        self.env['CONTENT_LENGTH'] = '9999'
        self.request()
        self.assertEqual(self.response.status_code, 400)
        self.assertEqual(self.response.body, 'invalid JSON payload')

    def test_malformed_payload_is_rejected(self):
        self.set_payload('blarg')
        self.request()
        self.assertEqual(self.response.status_code, 400)
        self.assertEqual(self.response.body, 'invalid JSON payload')

    def test_unsigned_payload_is_rejected(self):
        self.set_secret('blarg')
        self.set_json_payload({})
        self.request()
        self.assertEqual(self.response.status_code, 400)
        self.assertEqual(self.response.body, 'malformed signature')
        self.assertEqual(self.process_payload_arg, None)

    def test_invalid_hmac_alg_is_rejected(self):
        self.set_secret('blarg')
        self.set_json_payload({})
        self.set_signature('boop=blah')
        self.request()
        self.assertEqual(self.response.status_code, 400)
        self.assertEqual(self.response.body,
                         'invalid or unsupported hash algorithm')
        self.assertEqual(self.process_payload_arg, None)

    def test_invalid_signature_digest_is_rejected(self):
        self.set_secret('blarg')
        self.set_json_payload({})
        self.set_signature('sha1=blah')
        self.request()
        self.assertEqual(self.response.status_code, 400)
        self.assertEqual(self.response.body, 'invalid signature digest')
        self.assertEqual(self.process_payload_arg, None)

    def test_valid_signature_is_accepted(self):
        payload = {"zen": "Design for failure."}
        self.set_signed_json_payload(payload)
        self.request()
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.body, 'Thanks!')
        self.assertEqual(self.process_payload_arg, payload)

class MiscTests(unittest.TestCase):
    '''
    Test suite for miscellaneous functions and such.
    '''

    def test_get_current_git_head_works(self):
        self.assertRegexpMatches(get_current_git_head(), '^refs/heads')

if __name__ == '__main__':
    main()
