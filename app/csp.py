from app import csrf
from flask import current_app, make_response, request, Response, url_for

from hashlib import sha256
from base64 import b64encode
import functools

def add_header(response):
    '''
    Add a Content Security Policy (CSP) header to the given response.
    '''

    if request.path.startswith(url_for('admin.index')):
        # Ugh, flask-admin has inline scripts. Since only a handful of
        # users will have access to this view anyways, just disable CSP
        # for it.
        return response

    script_src = [
        "'self'",
        "use.typekit.net"
    ]

    if current_app.config.get('GA_TRACKING_CODE'):
        script_src.append('www.google-analytics.com')

    if current_app.config.get('PINGDOM_RUM_ID'):
        script_src.append('rum-static.pingdom.net')

    if hasattr(response, '_csp_script_src'):
        script_src += response._csp_script_src

    if current_app.debug and "'unsafe-inline'" not in script_src:
        # https://github.com/mgood/flask-debugtoolbar/issues/88
        m = sha256()
        m.update("var DEBUG_TOOLBAR_STATIC_PATH = '/_debug_toolbar/static/'")
        script_src.append("'sha256-%s'" % b64encode(m.digest()))

    response.headers.add(
        'Content-Security-Policy-Report-Only',
        '; '.join([
            'script-src %s' % ' '.join(script_src),
            'report-uri %s' % current_app.config.get('CSP_REPORT_URI',
                                                     '/csp-report')
        ])
    )
    return response

def script_src(source_list):
    '''
    Add additional script-src sources to the CSP header.
    '''

    def decorator(func):
        @functools.wraps(func)
        def func_wrapper(*args, **kwargs):
            response = make_response(func(*args, **kwargs))
            response._csp_script_src = source_list
            return response
        return func_wrapper
    return decorator

def init_app(app):
    app.after_request(add_header)

    @app.route('/csp-report', methods=['POST'])
    @csrf.exempt
    def csp_report():
        report = True
        if request.data:
            if 'safari-extension://' in request.data:
                report = False
            if (current_app.debug
                and 'DEBUG_TOOLBAR_STATIC_PATH' in request.data):
                # https://bugzilla.mozilla.org/show_bug.cgi?id=1026520
                report = False
        else:
            report = False

        if not report:
            return Response('CSP violation NOT reported.',
                            mimetype='text/plain')

        current_app.logger.error('CSP violation reported: %s' % request.data)
        return Response('CSP violation reported.', mimetype='text/plain')
