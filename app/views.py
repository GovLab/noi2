'''
NoI Views

All views in the app, as a blueprint
'''

from flask import (Blueprint, render_template, request, flash,
                   redirect, url_for, current_app, abort)
from flask_babel import lazy_gettext, gettext
from flask_login import login_required, current_user

from app import (QUESTIONNAIRES_BY_ID, MIN_QUESTIONS_TO_JOIN, LEVELS, l10n,
                 LEVELS_BY_SCORE, mail, stats, cache, blog_posts)
from app.models import (db, User, UserLanguage, UserExpertiseDomain,
                        UserSkill, Event, SharedMessageEvent, Email,
                        skills_to_percentages)

from app.forms import (UserForm, SearchForm, SharedMessageForm, PictureForm,
                       RegisterStep2Form, ChangeLocaleForm, InviteForm)

from sqlalchemy import func, desc, or_

from urllib import urlencode
import mimetypes
import functools
import json

views = Blueprint('views', __name__)  # pylint: disable=invalid-name

def json_blob(**kwargs):
    '''
    Converts the given keyword args into a serialized JSON blob. Useful
    as an alternative to Jinja's tojson filter since the content is
    still marked as unsafe (so it will be HTML-escaped).
    '''

    return json.dumps(kwargs)

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
        return render_template('main.html',
                               viz_data=get_network_viz_data(),
                               change_locale_form=ChangeLocaleForm())


@views.route('/about')
def about_page():
    '''
    NoI about page.
    '''
    return render_template('about.html')


@views.route('/terms')
def terms_and_conditions():
    '''
    NoI terms and conditions page.
    '''
    return render_template('terms_and_conditions.html')


@views.route('/faq')
def faq():
    '''
    NoI FAQ page.
    '''
    return render_template('faq.html')

def set_user_picture(user, picture):
    user.upload_picture(
        picture.data,
        mimetype=mimetypes.guess_type(picture.data.filename)[0]
    )

@views.route('/me/picture/remove', methods=['POST'])
@full_registration_required
def my_profile_remove_picture():
    current_user.remove_picture()
    db.session.commit()
    return ('', 204)

@views.route('/me/picture', methods=['POST'])
@full_registration_required
def my_profile_upload_picture():
    form = PictureForm()
    # TODO: Is it possible for 'X-Upload-Too-Big' to be in request.headers,
    # and if so, should we deal with it?
    if form.validate():
        if form.picture.has_file():
            set_user_picture(current_user, form.picture)
            db.session.add(current_user)
            db.session.commit()
            return ('', 204)
    abort(400)

@views.route('/me', methods=['GET', 'POST'])
@full_registration_required
def my_profile():
    '''
    Show user their profile, let them edit it
    '''
    form = UserForm(obj=current_user)
    if 'X-Upload-Too-Big' in request.headers:
        form.picture.errors = ('Sorry, the picture you tried to upload was too large',)
    if request.method == 'POST':

        if form.validate():
            form.populate_obj(current_user)

            if form.picture.has_file():
                set_user_picture(current_user, form.picture)

            db.session.add(current_user)
            db.session.commit()
            flash(gettext('Your profile has been saved.'))
            return redirect(url_for('views.my_expertise'))
        else:
            flash(gettext(u'Could not save, please correct errors.'))

    return render_template(
        'my-profile.html',
        form=form,
        page_config_json=json_blob(
            UPLOAD_PICTURE_URL=url_for('views.my_profile_upload_picture'),
            UPLOAD_PICTURE_SUCCESS=gettext("Your user picture has been changed."),
            UPLOAD_PICTURE_ERROR=gettext("An error occurred when uploading your user picture."),
            REMOVE_PICTURE_URL=url_for('views.my_profile_remove_picture'),
            REMOVE_PICTURE_CONFIRM=gettext("Do you really want to remove your profile picture?"),
            REMOVE_PICTURE_SUCCESS=gettext("Your profile picture has been removed."),
            REMOVE_PICTURE_ERROR=gettext("An error occurred when removing your profile picture."),
        )
    )

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

    if current_app.debug:
        if 'qa' in request.args:
            questions_answered = int(request.args['qa'])
        # This will show up in the debug toolbar.
        current_app.logger.debug(
            "Use the 'qa' query string arg to tweak the number of questions "
            "answered."
        )

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
    Present user with instructions and a link to the first unanswered
    question in the given area.
    '''

    questionnaire = get_area_questionnaire_or_404(areaid)
    skills = current_user.skill_levels
    for i in range(len(questionnaire['questions'])):
        question = questionnaire['questions'][i]
        if question['id'] not in skills:
            break

    return render_register_step_3(
        next_url=url_for('views.register_step_3_area_question',
                         areaid=areaid, questionid=str(i+1)),
        areaid=areaid,
        MIN_QUESTIONS_TO_JOIN=MIN_QUESTIONS_TO_JOIN
    )

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
            return redirect(url_for('views.activity'))

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


@views.route('/confirm/success')
@login_required
def confirmation_success():
    # In the future, we can make this view redirect the user to
    # whatever they wanted to do that required confirmation.
    return redirect(url_for('views.activity'))


def render_user_profile(userid=None, **kwargs):
    if userid is None:
        user = current_user
    else:
        user = User.query_in_deployment().filter_by(id=userid).first_or_404()

    area_scores = user.get_area_scores()

    kwargs['user'] = user
    overview_data = {}
    viz_data = []
    kwargs['overview_data'] = overview_data
    for qid, score_info in area_scores.items():
        score = score_info['max_score']
        if score is not None:
            # Update overview data.
            if score not in overview_data:
                overview_data[score] = []
            overview_data[score].append(QUESTIONNAIRES_BY_ID[qid])

            # Update visualization data.

            # TODO: This is very similar to the treemap code in
            # views.network, consider refactoring.

            s = score_info['skills']
            area_info = {
                'name': QUESTIONNAIRES_BY_ID[qid]['name'],
                'questionnaire_id': qid,
                'total': s['learn'] + s['explain'] + s['connect'] + s['do']
            }
            area_info.update(skills_to_percentages(s))
            viz_data.append(area_info)
    kwargs['viz_data'] = sorted(
        viz_data,
        key=lambda area_info: area_info['total'],
        reverse=True
    )

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
    If the user has never answered questions in this area before, show
    them some introductory text; otherwise, automatically redirect the
    user to the first unanswered question in the given area.
    '''

    questionnaire = get_area_questionnaire_or_404(areaid)
    skills = current_user.skill_levels
    first_unanswered = None
    total_answered = 0

    for i in range(len(questionnaire['questions'])):
        question = questionnaire['questions'][i]
        if question['id'] in skills:
            total_answered += 1
        elif first_unanswered is None:
            first_unanswered = i+1

    if first_unanswered is None:
        first_unanswered = i + 1

    next_url = url_for('views.my_expertise_area_question',
                       areaid=areaid, questionid=str(first_unanswered))

    if total_answered == 0:
        return render_user_profile(active_tab='expertise',
                                   in_questionnaire=True,
                                   areaid=areaid,
                                   next_url=next_url)
    return redirect(next_url)

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
        in_questionnaire=True,
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
        if len(emails) != 1:
            abort(501)
        users = User.query_in_deployment().filter(User.email.in_(emails))
        email = db.session.query(Email).filter(
            Email.from_user_id == current_user.id,
            Email.to_user_id == users[0].id
        ).first()
        if email is None:
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
    form = SearchForm(request.args, csrf_enabled=False)
    if not form.validate():
        return render_template('search.html', form=form)
    else:
        result_tabs = []
        active_result_tab = None
        query = User.query_in_deployment() #pylint: disable=no-member

        if (form.questionnaire_area.data and
            form.questionnaire_area.data != 'ZZ'):
            questionnaire_id = form.questionnaire_area.data
            num_skills_column = func.count(UserSkill.id).label('num_skills')
            query = query.add_column(num_skills_column).\
                filter(UserSkill.user_id == User.id).\
                filter(UserSkill.name.like(questionnaire_id + "_%")).\
                filter(UserSkill.level == form.skill_level.data).\
                group_by(User).\
                order_by(num_skills_column.desc())

            base_args = request.args.copy()
            if 'skill_level' in base_args:
                del base_args['skill_level']

            tab_names = (
                ('LEVEL_I_CAN_DO_IT', gettext('Practitioners')),
                ('LEVEL_I_CAN_EXPLAIN', gettext('Explainers')),
                ('LEVEL_I_CAN_REFER', gettext('Connectors')),
                ('LEVEL_I_WANT_TO_LEARN', gettext('Peers')),
            )

            for level_id, tab_label in tab_names:
                tab_args = base_args.copy()
                tab_args['skill_level'] = str(LEVELS[level_id]['score'])
                tab_url = '%s?%s#results' % (
                    url_for('views.search'),
                    urlencode(tab_args)
                )
                if form.skill_level.data == LEVELS[level_id]['score']:
                    active_result_tab = level_id
                result_tabs.append((level_id, tab_label, tab_url))
        else:
            # Add fake rank of 0 for now
            query = query.add_column('0')

        if form.country.data and form.country.data != 'ZZ':
            query = query.filter(User.country == form.country.data)

        if form.locale.data and form.locale.data != 'ZZ':
            query = query.join(User.languages).filter(UserLanguage.locale.in_(
                [form.locale.data]))

        if (form.expertise_domain_name.data and
            form.expertise_domain_name.data != 'ZZ'):
            query = query.join(User.expertise_domains).filter(
                UserExpertiseDomain.name.in_(
                    [form.expertise_domain_name.data]
                )
            )

        if form.fulltext.data:
            ftquery = "%" + form.fulltext.data + "%"
            query = query.filter(or_(
                User.first_name.ilike(ftquery),
                User.last_name.ilike(ftquery),
                User.organization.ilike(ftquery),
                User.position.ilike(ftquery),
                User.projects.ilike(ftquery),
                (User.first_name + ' ' + User.last_name).ilike(ftquery)
            ))

        return render_template('search.html',
                               result_tabs=result_tabs,
                               active_result_tab=active_result_tab,
                               form=form,
                               results=query.limit(20).all())

def render_matches(active_tab, level_name):
    level_score = LEVELS[level_name]['score']
    matches = current_user.match(level=level_score)

    return render_template('match-me.html',
                           level_score=level_score,
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

    return redirect(url_for('views.match_practitioners'))

def get_latest_events(pageid=1):
    return Event.query_in_deployment().order_by(desc(Event.created_at)).\
           paginate(pageid)

@views.route('/activity/page/<pageid>')
def activity_page(pageid):
    '''
    Individual page for activity stream (for infinite scrolling).
    '''

    try:
        pageid = int(pageid)
        if pageid <= 0:
            raise ValueError()
    except ValueError:
        abort(404)

    return render_template('_activity_events.html',
                           events=get_latest_events(pageid))

@views.route('/activity', methods=['GET', 'POST'])
def activity():
    '''
    View for the activity feed of recent events.
    '''

    events = get_latest_events()
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
        'blog_posts': get_blog_posts(),
        'page_config_json': json_blob(
            LOADING_TEXT=gettext("Loading...")
        ),
        'most_complete_profiles': User.get_most_complete_profiles(limit=5),
        'most_connected_profiles': User.get_most_connected_profiles(limit=5)
    })

@cache.cached(key_prefix='blog_posts', timeout=60*5)
def get_blog_posts():
    url = current_app.config.get('BLOG_POSTS_RSS_URL')
    if url is None: return []
    return blog_posts.get_and_summarize(url)

@cache.cached(key_prefix='network_viz_data', timeout=60)
def get_network_viz_data():
    counts = stats.get_questionnaire_counts()

    viz_data = []
    for qid, s in counts.items():
        area_info = {
            'name': QUESTIONNAIRES_BY_ID[qid]['name'],
            'total': s['learn'] + s['explain'] + s['connect'] + s['do']
        }
        area_info.update(skills_to_percentages(s))
        viz_data.append(area_info)
    viz_data = sorted(viz_data, key=lambda area_info: area_info['total'],
                      reverse=True)
    return viz_data

@views.route('/network')
@full_registration_required
def network():
    '''
    View the network.
    '''

    viz_data = get_network_viz_data()
    return render_template('network.html', viz_data=viz_data)

@views.route('/feedback')
def feedback():
    '''
    Feedback page.
    '''
    return render_template('feedback.html', **{})

@views.route('/change-locale', methods=['POST'])
def change_locale():
    '''
    Change the user's current locale for interacting with the site.
    '''

    change_locale_form=ChangeLocaleForm()

    if change_locale_form.validate():
        l10n.change_session_locale(change_locale_form.locale.data)
    else:
        abort(400)

    return redirect(request.referrer or '/')

@views.route('/settings')
@full_registration_required
def settings():
    '''
    User settings page.
    '''

    return render_template('settings.html',
                           change_locale_form=ChangeLocaleForm())

@views.route('/invite', methods=['GET', 'POST'])
@full_registration_required
def invite():
    '''
    Invite another human to join the site.
    '''

    form = InviteForm()

    if request.method == 'POST':
        if form.validate():
            site_url = 'https://%s' % current_app.config['NOI_DEPLOY']
            sender = current_app.config['MAIL_USERNAME']
            mail.send_message(
                subject=gettext(
                    "%(user)s would like you to join the Network of "
                    "Innovators!",
                    user=current_user.full_name,
                ),
                body=gettext(
                    "%(user)s has invited you to join the "
                    "Network of Innovators -- a new skill-sharing network "
                    "for government and civic innovators worldwide.\n\n"
                    "Join today. It's FREE. And in just a few minutes, "
                    "you can get matched with innovators from around the "
                    "world.\n\n"
                    "Build your network now at %(url)s.",
                    user=current_user.full_name,
                    url=site_url,
                ),
                sender=sender,
                recipients=[form.email.data]
            )
            flash(gettext("Invitation sent!"))
            return redirect(url_for('views.invite'))
        else:
            flash(gettext("Your form submission was invalid."), "error")

    return render_template('invite.html', form=form)
