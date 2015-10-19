'''
NoI Views

All views in the app, as a blueprint
'''

from flask import (Blueprint, render_template, request, flash,
                   redirect, url_for, current_app, abort)
from flask_babel import lazy_gettext, gettext
from flask_login import login_required, current_user

from app import QUESTIONNAIRES_BY_ID, MIN_QUESTIONS_TO_JOIN, LEVELS
from app.models import (db, User, UserLanguage, UserExpertiseDomain,
                        UserSkill, Event, SharedMessageEvent)

from app.forms import (UserForm, SearchForm, SharedMessageForm,
                       RegisterStep2Form)

from sqlalchemy import func, desc
from sqlalchemy.dialects.postgres import array

from boto.s3.connection import S3Connection

import mimetypes
import functools

views = Blueprint('views', __name__)  # pylint: disable=invalid-name

def get_best_registration_step_url(user):
    '''
    Assuming the user is not yet fully registered, returns the URL
    of the most appropriate step in the registration flow for
    them to complete.
    '''

    if len(user.skills) > 0 or RegisterStep2Form.is_not_empty(user):
        return url_for('views.register_step_3')
    return url_for('views.register_step_2')

def full_registration_required(func):
    '''
    A view decorator that requires both login *and* full completion
    of the registration process. If the user isn't logged in, they
    are redirected to login; if they are logged in but not fully
    registered, they are redirected to complete the registration
    process.
    '''

    @functools.wraps(func)
    @login_required
    def decorated_view(*args, **kwargs):
        if not current_user.has_fully_registered:
            return redirect(get_best_registration_step_url(current_user))
        return func(*args, **kwargs)

    return decorated_view

@views.route('/')
def main_page():
    '''
    Main NoI page: forward to activity page if logged in already.
    '''
    if current_user.is_authenticated():
        return redirect(url_for('views.activity'))
    else:
        return render_template('main.html', SKIP_NAV_BAR=False)


@views.route('/about')
def about_page():
    '''
    NoI about page.
    '''
    return render_template('about.html')


@views.route('/me', methods=['GET', 'POST'])
@full_registration_required
def my_profile():
    '''
    Show user their profile, let them edit it
    '''
    form = UserForm(obj=current_user)
    if 'X-Upload-Too-Big' in request.headers:
        form.picture.errors = ('Sorry, the picture you tried to upload was too large',)
    if request.method == 'GET':
        return render_template('my-profile.html', form=form)
    elif request.method == 'POST':

        if form.validate():
            form.populate_obj(current_user)

            if form.picture.has_file():
                conn = S3Connection(current_app.config['S3_ACCESS_KEY_ID'],
                                    current_app.config['S3_SECRET_ACCESS_KEY'])
                bucket = conn.get_bucket(current_app.config['S3_BUCKET_NAME'])
                bucket.make_public(recursive=False)

                mimetype = mimetypes.guess_type(form.picture.data.filename)[0]

                k = bucket.new_key(current_user.picture_path)
                k.set_metadata('Content-Type', mimetype)
                k.set_contents_from_file(form.picture.data)
                k.make_public()

                current_user.has_picture = True

            db.session.add(current_user)
            db.session.commit()
            flash(gettext('Your profile has been saved.'))
            return redirect(url_for('views.my_expertise'))
        else:
            flash(gettext(u'Could not save, please correct errors.'))

        return render_template('my-profile.html', form=form)

def get_area_questionnaire_or_404(areaid):
    '''
    Return the questionnaire for the given area ID or raise a 404.
    '''

    questionnaire = QUESTIONNAIRES_BY_ID.get(areaid)
    if questionnaire is None:
        abort(404)
    return questionnaire

def render_register_step_3(**kwargs):
    questions_answered = len(current_user.skills)

    return render_template(
        'register-step-3.html',
        user_can_join=questions_answered >= MIN_QUESTIONS_TO_JOIN,
        questions_left=MIN_QUESTIONS_TO_JOIN - questions_answered,
        **kwargs
    )

@views.route('/register/step/3')
@login_required
def register_step_3():
    '''
    Provide the user with a list of expertise areas to choose from.
    '''

    return render_register_step_3()

@views.route('/register/step/3/<areaid>')
@login_required
def register_step_3_area(areaid):
    '''
    Redirect the user to the first unanswered question in the given area.
    '''

    questionnaire = get_area_questionnaire_or_404(areaid)
    skills = current_user.skill_levels
    for i in range(len(questionnaire['questions'])):
        question = questionnaire['questions'][i]
        if question['id'] not in skills:
            break
    return redirect(url_for('views.register_step_3_area_question',
                            areaid=areaid, questionid=str(i+1)))

@views.route('/register/step/3/<areaid>/<questionid>',
             methods=['GET', 'POST'])
@login_required
def register_step_3_area_question(areaid, questionid):
    '''
    Ask the user the given question number in the given area.
    '''

    questionnaire = get_area_questionnaire_or_404(areaid)
    max_questionid = len(questionnaire['questions'])
    try:
        questionid = int(questionid)
        if questionid < 1 or questionid > max_questionid:
            raise ValueError
        question = questionnaire['questions'][questionid - 1]
        next_questionid = None
        prev_questionid = None
        if questionid > 1:
            prev_questionid = questionid - 1
        if questionid < max_questionid:
            next_questionid = questionid + 1
    except ValueError:
        abort(404)

    if request.method == 'POST':
        current_user.set_skill(question['id'], request.form.get('answer'))
        db.session.add(current_user)
        db.session.commit()
        if len(current_user.skills) >= MIN_QUESTIONS_TO_JOIN:
            current_user.set_fully_registered()
            db.session.commit()
        if next_questionid:
            return redirect(url_for(
                'views.register_step_3_area_question',
                areaid=areaid, questionid=next_questionid
            ))
        else:
            return redirect(url_for('views.register_step_3'))

    return render_register_step_3(
        question=question,
        areaid=areaid,
        questionid=questionid,
        next_questionid=next_questionid,
        prev_questionid=prev_questionid,
        max_questionid=max_questionid,
    )

@views.route('/register/step/2', methods=['GET', 'POST'])
@login_required
def register_step_2():
    '''
    Let user edit a simplified version of their profile as part
    of their registration.
    '''

    form = RegisterStep2Form(obj=current_user)
    if request.method == 'POST':
        if form.validate():
            form.populate_obj(current_user)
            db.session.add(current_user)
            db.session.commit()
            return redirect(url_for('views.register_step_3'))
        else:
            flash(gettext(u'Could not save, please correct errors below'))

    return render_template('register-step-2.html', form=form)


def render_user_profile(userid=None, **kwargs):
    if userid is None:
        user = current_user
    else:
        user = User.query_in_deployment().filter_by(id=userid).first_or_404()
    kwargs['user'] = user
    return render_template('user-profile.html', **kwargs)


@views.route('/user/<userid>')
@full_registration_required
def get_user(userid):
    '''
    Public-facing profile view
    '''

    return render_user_profile(userid)


@views.route('/user/<userid>/expertise/')
@full_registration_required
def get_user_expertise(userid):
    '''
    Public-facing profile view, with expertise tab selected
    '''

    return render_user_profile(userid, active_tab='expertise')


@views.route('/user/<userid>/expertise/<areaid>')
@full_registration_required
def get_user_expertise_area(userid, areaid):
    '''
    Public-facing profile view, with expertise tab selected
    '''

    questionnaire = get_area_questionnaire_or_404(areaid)
    return render_user_profile(
        userid,
        active_tab='expertise',
        areaid=areaid
        )


@views.route('/my-expertise/')
@full_registration_required
def my_expertise():
    '''
    Show user profile progress.
    '''

    return render_user_profile(active_tab='expertise')


# TODO: This code is largely copied/pasted from
# register_step_3_area, consider refactoring.
@views.route('/my-expertise/<areaid>')
@full_registration_required
def my_expertise_area(areaid):
    '''
    Redirect the user to the first unanswered question in the given area.
    '''

    questionnaire = get_area_questionnaire_or_404(areaid)
    skills = current_user.skill_levels
    for i in range(len(questionnaire['questions'])):
        question = questionnaire['questions'][i]
        if question['id'] not in skills:
            break
    return redirect(url_for('views.my_expertise_area_question',
                            areaid=areaid, questionid=str(i+1)))

# TODO: This code is largely copied/pasted from
# register_step_3_area_question, consider refactoring.
@views.route('/my-expertise/<areaid>/<questionid>',
             methods=['GET', 'POST'])
@full_registration_required
def my_expertise_area_question(areaid, questionid):
    '''
    Ask the user the given question number in the given area.
    '''

    questionnaire = get_area_questionnaire_or_404(areaid)
    max_questionid = len(questionnaire['questions'])
    try:
        questionid = int(questionid)
        if questionid < 1 or questionid > max_questionid:
            raise ValueError
        question = questionnaire['questions'][questionid - 1]
        next_questionid = None
        prev_questionid = None
        if questionid > 1:
            prev_questionid = questionid - 1
        if questionid < max_questionid:
            next_questionid = questionid + 1
    except ValueError:
        abort(404)

    if request.method == 'POST':
        current_user.set_skill(question['id'], request.form.get('answer'))
        db.session.add(current_user)
        db.session.commit()
        if next_questionid:
            return redirect(url_for(
                'views.my_expertise_area_question',
                areaid=areaid, questionid=next_questionid
            ))
        else:
            return redirect(url_for('views.my_expertise'))

    return render_user_profile(
        active_tab='expertise',
        question=question,
        areaid=areaid,
        questionid=questionid,
        next_questionid=next_questionid,
        prev_questionid=prev_questionid,
        max_questionid=max_questionid,
    )


@views.route('/email', methods=['POST'])
@full_registration_required
def email():
    '''
    Mark that an email could have been sent to recipients in post
    '''
    emails = request.form.getlist('emails[]')
    if emails:
        users = User.query_in_deployment().filter(User.email.in_(emails))
        event = current_user.email_connect(users)
        db.session.commit()
        event.set_total_connections()
        db.session.commit()
    return ('', 204)

@views.route('/tutorial', methods=['POST'])
@full_registration_required
def tutorial():
    '''
    Save in the DB that user has seen a tutorial step.
    '''
    current_user.tutorial_step = int(request.form.get('step'))
    db.session.add(current_user)
    db.session.commit()
    return ('', 204)

@views.route('/search')
@full_registration_required
def search():
    '''
    Generic search page
    '''
    form = SearchForm(request.args)
    if not form.country.data:
        return render_template('search.html', form=form)
    else:
        # Add fake rank of 0 for now
        query = User.query_in_deployment().add_column('0')  #pylint: disable=no-member

        if form.country.data and form.country.data != 'ZZ':
            query = query.filter(User.country == form.country.data)

        if form.locales.data:
            query = query.join(User.languages).filter(UserLanguage.locale.in_(
                form.locales.data))

        if form.expertise_domain_names.data:
            query = query.join(User.expertise_domains).filter(UserExpertiseDomain.name.in_(
                form.expertise_domain_names.data))

        if form.fulltext.data:
            query = query.filter(func.to_tsvector(func.array_to_string(array([
                User.first_name, User.last_name, User.organization, User.position,
                User.projects, UserSkill.name]), ' ')).op('@@')(
                    func.plainto_tsquery(form.fulltext.data))).filter(
                        UserSkill.user_id == User.id)

        # TODO ordering by relevance
        return render_template('search.html',
                               form=form,
                               results=query.limit(20).all())

def render_matches(active_tab, level_name):
    matches = current_user.match(level=LEVELS[level_name]['score'])

    return render_template('match-me.html',
                           active_tab=active_tab, matches=matches)

@views.route('/match/connectors')
@full_registration_required
def match_connectors():
    return render_matches('connectors', 'LEVEL_I_CAN_REFER')

@views.route('/match/peers')
@full_registration_required
def match_peers():
    return render_matches('peers', 'LEVEL_I_WANT_TO_LEARN')

@views.route('/match/explainers')
@full_registration_required
def match_explainers():
    return render_matches('explainers', 'LEVEL_I_CAN_EXPLAIN')

@views.route('/match/practitioners')
@full_registration_required
def match_practitioners():
    return render_matches('practitioners', 'LEVEL_I_CAN_DO_IT')

@views.route('/match')
@full_registration_required
def match():
    '''
    'Match Me' page.
    '''

    return redirect(url_for('views.match_connectors'))

@views.route('/activity', methods=['GET', 'POST'])
def activity():
    '''
    View for the activity feed of recent events.
    '''

    events = Event.query_in_deployment().order_by(desc(Event.created_at)).\
             limit(50).all()
    shared_message_form = SharedMessageForm()

    if request.method == 'POST':
        if not current_user.is_authenticated():
            flash(gettext(u'You must log in to post a message.'), 'error')
        elif not current_user.display_in_search:
            flash(gettext(u'We need your name before you can post a message.'), 'error')
        elif shared_message_form.validate():
            data = shared_message_form.message.data
            msg = SharedMessageEvent.from_user(
                current_user,
                message=data
            )
            db.session.add(msg)
            db.session.commit()
            flash(gettext(u'Message posted!'))
            return redirect(url_for('views.activity'))

    return render_template('activity.html', **{
        'user': current_user,
        'events': events,
        'most_complete_profiles': User.get_most_complete_profiles(limit=5),
        'most_connected_profiles': User.get_most_connected_profiles(limit=5)
    })

@views.route('/network')
@full_registration_required
def network():
    '''
    View the network.
    '''

    return render_template('network.html')

@views.route('/feedback')
def feedback():
    '''
    Feedback page.
    '''
    return render_template('feedback.html', **{})
