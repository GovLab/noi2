from flask import request, session
import flask_babel
from speaklater import make_lazy_string
from babel import Locale

DEFAULT_LOCALE = Locale('en')

TRANSLATIONS = [Locale('es')]
VALID_LOCALES = [DEFAULT_LOCALE] + TRANSLATIONS
VALID_LOCALE_CODES = [str(l) for l in VALID_LOCALES]


def configure_app(app):
    def lazy_gettext(string):
        '''
        Like flask_babel's lazy_gettext, but doesn't interpolate strings. This
        is required for integration with flask_security, which does its
        own string interpolation but doesn't support i18n.

        For more information, see: https://github.com/GovLab/noi2/issues/41
        '''

        def gettext_no_interpolate(string):
            t = flask_babel.get_translations()
            if t is None:
                return string
            return t.ugettext(string)

        return make_lazy_string(gettext_no_interpolate, string)

    app.config['SECURITY_MSG_UNAUTHORIZED'] = (
        lazy_gettext('You do not have permission to view this resource.'), 'error')
    app.config['SECURITY_MSG_EMAIL_CONFIRMED'] = (
        lazy_gettext('Thank you. Your email has been confirmed.'), 'success')
    app.config['SECURITY_MSG_ALREADY_CONFIRMED'] = (
        lazy_gettext('Your email has already been confirmed.'), 'info')
    app.config['SECURITY_MSG_INVALID_CONFIRMATION_TOKEN'] = (
        lazy_gettext('Invalid confirmation token.'), 'error')
    app.config['SECURITY_MSG_EMAIL_ALREADY_ASSOCIATED'] = (
        lazy_gettext('%(email)s is already associated with an account.'), 'error')
    app.config['SECURITY_MSG_PASSWORD_MISMATCH'] = (
        lazy_gettext('Password does not match'), 'error')
    app.config['SECURITY_MSG_RETYPE_PASSWORD_MISMATCH'] = (
        lazy_gettext('Passwords do not match'), 'error')
    app.config['SECURITY_MSG_INVALID_REDIRECT'] = (
        lazy_gettext('Redirections outside the domain are forbidden'), 'error')
    app.config['SECURITY_MSG_PASSWORD_RESET_REQUEST'] = (
        lazy_gettext('Instructions to reset your password have been sent to %(email)s.'), 'info')
    app.config['SECURITY_MSG_PASSWORD_RESET_EXPIRED'] = (
        lazy_gettext('You did not reset your password within %(within)s. New '
                     'instructions have been sent to %(email)s.'), 'error')
    app.config['SECURITY_MSG_INVALID_RESET_PASSWORD_TOKEN'] = (
        lazy_gettext('Invalid reset password token.'), 'error')
    app.config['SECURITY_MSG_CONFIRMATION_REQUIRED'] = (
        lazy_gettext('Email requires confirmation.'), 'error')
    app.config['SECURITY_MSG_CONFIRMATION_REQUEST'] = (
        lazy_gettext('Confirmation instructions have been sent to %(email)s.'), 'info')
    app.config['SECURITY_MSG_CONFIRMATION_EXPIRED'] = (
        lazy_gettext('You did not confirm your email within %(within)s. New '
                     'instructions to confirm your email have been sent to '
                     '%(email)s.'), 'error')
    app.config['SECURITY_MSG_LOGIN_EXPIRED'] = (
        lazy_gettext('You did not login within %(within)s. New instructions to '
                     'login have been sent to %(email)s.'), 'error')
    app.config['SECURITY_MSG_LOGIN_EMAIL_SENT'] = (
        lazy_gettext('Instructions to login have been sent to %(email)s.'), 'success')
    app.config['SECURITY_MSG_INVALID_LOGIN_TOKEN'] = (
        lazy_gettext('Invalid login token.'), 'error')
    app.config['SECURITY_MSG_DISABLED_ACCOUNT'] = (
        lazy_gettext('Account is disabled.'), 'error')
    app.config['SECURITY_MSG_EMAIL_NOT_PROVIDED'] = (
        lazy_gettext('Email not provided'), 'error')
    app.config['SECURITY_MSG_INVALID_EMAIL_ADDRESS'] = (
        lazy_gettext('Invalid email address'), 'error')
    app.config['SECURITY_MSG_PASSWORD_NOT_PROVIDED'] = (
        lazy_gettext('Password not provided'), 'error')
    app.config['SECURITY_MSG_PASSWORD_NOT_SET'] = (
        lazy_gettext('No password is set for this user'), 'error')
    app.config['SECURITY_MSG_PASSWORD_INVALID_LENGTH'] = (
        lazy_gettext('Password must be at least 6 characters'), 'error')
    app.config['SECURITY_MSG_USER_DOES_NOT_EXIST'] = (
        lazy_gettext('Specified user does not exist'), 'error')
    app.config['SECURITY_MSG_INVALID_PASSWORD'] = (
        lazy_gettext('Invalid password'), 'error')
    app.config['SECURITY_MSG_PASSWORDLESS_LOGIN_SUCCESSFUL'] = (
        lazy_gettext('You have successfuly logged in.'), 'success')
    app.config['SECURITY_MSG_PASSWORD_RESET'] = (
        lazy_gettext('You successfully reset your password and you have been '
                     'logged in automatically.'), 'success')
    app.config['SECURITY_MSG_PASSWORD_IS_THE_SAME'] = (
        lazy_gettext('Your new password must be different than your previous password.'), 'error')
    app.config['SECURITY_MSG_PASSWORD_CHANGE'] = (
        lazy_gettext('You successfully changed your password.'), 'success')
    app.config['SECURITY_MSG_LOGIN'] = (
        lazy_gettext('Please log in to access this page.'), 'info')
    app.config['SECURITY_MSG_REFRESH'] = (
        lazy_gettext('Please reauthenticate to access this page.'), 'info')

def init_app(app):
    babel = app.extensions['babel']

    @babel.localeselector
    def get_locale():
        if 'locale' in session and session['locale'] in VALID_LOCALE_CODES:
            return session['locale']
        return request.accept_languages.best_match(VALID_LOCALE_CODES)

    # This forces any "lazy strings" like those returned by
    # lazy_gettext() to be evaluated.
    app.login_manager.localize_callback = unicode

def change_session_locale(locale, session=session):
    if locale in VALID_LOCALE_CODES:
        session['locale'] = str(locale)
