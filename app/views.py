'''
NoI Views

All views in the app, as a blueprint
'''

from flask import (Blueprint, render_template, session, request, flash,
                   redirect, url_for)
from flask_babel import lazy_gettext, gettext
from flask_login import login_required, current_user

from app import CONTENT
from app.models import db, User, UserLanguage, UserExpertiseDomain
from app.forms import UserForm, SearchForm

from sqlalchemy import func, desc
from sqlalchemy.dialects.postgres import array

views = Blueprint('views', __name__)  # pylint: disable=invalid-name


@views.route('/')
def main_page():
    '''
    Main NoI page
    '''
    return render_template('main.html', **{'SKIP_NAV_BAR': False})


@views.route('/about')
def about_page():
    '''
    NoI about page.
    '''
    #TODO this should vary based off of deployment
    return render_template('about.html', **{})


#@views.route('/login', methods=['GET', 'POST'])
#def login():
#    print session
#    if request.method == 'GET':
#        return render_template('login-page.html', **{'SKIP_NAV_BAR': False})
#    if request.method == 'POST':
#        social_login = json.loads(request.form.get('social-login'))
#        session['social-login'] = social_login
#        userid = social_login['userid']
#        userProfile = db.getUser(userid)
#        if userProfile:
#            session['user-profile'] = userProfile
#        else:
#            db.createNewUser(userid, social_login['first_name'],
#            social_login['last_name'], social_login['picture'])
#            userProfile = db.getUser(userid)
#            session['user-profile'] = userProfile
#        flash('You are authenticated using your %s Credentials.' % social_login['idp'])
#        g.is_logged_in = True
#        return jsonify({'result': 0})


#@views.route('/logout')
#def logout():
#    idp = session['social-login']['idp']
#    session.clear()
#    return redirect(url_for('main_page', **{'logout': idp}))


#@views.route('/edit/<userid>', methods=['GET', 'POST'])
#def edit_user(userid):
#    if request.method == 'GET':
#        userProfile = db.getUser(userid)  # We get some stuff from the DB.
#        return render_template('my-profile.html',
#                               **{'userProfile': userProfile})
#
#    if current_user.id:
#        if request.method == 'POST' and userid == current_user.id:
#            userProfile = json.loads(request.form.get('me'))
#            session['user-profile'] = userProfile
#            db.updateCoreProfile(userProfile)
#            flash('Your profile has been saved.')
#            return render_template('my-profile.html', **{'userProfile': userProfile})


@views.route('/me', methods=['GET', 'POST'])
@login_required
def my_profile():
    '''
    Show user their profile, let them edit it
    '''
    form = UserForm(obj=current_user)
    if request.method == 'GET':
        return render_template('my-profile.html', form=form)
    elif request.method == 'POST':
        #userProfile = json.loads(request.form.get('me'))
        #session['user-profile'] = userProfile
        #db.updateCoreProfile(userProfile)
        #flash('Your profile has been saved. <br/>You may also want to <a'
        #      'href="/my-expertise">tell us what you know</a>.')
        #session['has_created_profile'] = True
        form.populate_obj(current_user)
        if form.validate():
            db.session.add(current_user)
            db.session.commit()
            flash(lazy_gettext('Your profile has been saved. <br/>You may also want to <a'
                               'href="/my-expertise">tell us what you know</a>.'))
        else:
            flash(lazy_gettext(u'Could not save, please correct errors below: {}'.format(
                form.errors)))

        return render_template('my-profile.html', form=form)


@views.route('/my-expertise', methods=['GET', 'POST'])
@login_required
def my_expertise():
    '''
    Allow user to edit their expertise
    '''
    #if 'social-login' not in session:
    #    flash('You need to be authenticated in order to fill your expertise.', 'error')
    #    return redirect(url_for('login'))
    #social_login = session['social-login']
    #userid = social_login['userid']
    if request.method == 'GET':
        return render_template('my-expertise.html', AREAS=CONTENT['areas'])
    elif request.method == 'POST':
        for k, val in request.form.iteritems():
            current_user.set_skill(k, val)
        db.session.add(current_user)
        db.session.commit()
        flash(lazy_gettext("""Your expertise has been updated.<br/>
        What you can do next:
        <ul>
        <li><a href="/search">Search for innovators</a></li>
        <li>Fill another expertise questionnaire below</li>
        <li>View your <a href="/user/{}">public profile</a></li>
        """).format(current_user.id))
        return render_template('my-expertise.html', AREAS=CONTENT['areas'])


@views.route('/dashboard')
def dashboard():
    '''
    Dashboard of what's happening on the platform.
    '''
    top_countries = db.session.query(func.count(User.id)) \
            .group_by(User.country) \
            .order_by(desc(func.count(User.id))).all()
    users = [{'latlng': u.latlng,
              'first_name': u.first_name,
              'last_name': u.last_name} for u in User.query.all()]
    occupations = db.session.query(func.count(User.id)) \
            .group_by(User.organization_type) \
            .order_by(desc(func.count(User.id))).all()

    return render_template('dashboard.html', **{'top_countries': top_countries,
                                                'ALL_USERS': users,
                                                'OCCUPATIONS': occupations})

#@views.route('/dashboard-2')
#def dashboard2():
#    return render_template('dashboard-2.html', **{'top_countries': top_countries})

#@views.route('/vcard/<userid>')
#def vcard(userid):
#    user = db.getUser(userid)
#    if user:
#        card = make_vCard(user['first_name'], user['last_name'], user['org'],
#        user['title'], user['email'], user['city'], user['country'])
#        return Response(card, mimetype='text/vcard')
#    else:
#        flash('This is does not correspond to a valid user.')
#        return redirect(url_for('main_page'))


@views.route('/user/<userid>')
def get_user(userid):
    '''
    Public-facing profile view
    '''
    user = User.query.get(userid)
    if user:
        #if 'social-login' in session:
        #    my_userid = session['social-login']['userid']
        #else:
        #    my_userid = 'anonymous'
        #query_info = {'user-agent': request.headers.get('User-Agent'),
        #              'type': '/user', 'userid': my_userid}
        #db.logQuery(my_userid, query_info)
        return render_template('user-profile.html', user=user)
    else:
        flash('This is does not correspond to a valid user.')
        return redirect(url_for('views.search'))


@views.route('/search', methods=['GET', 'POST'])
def search():
    '''
    Generic search page
    '''
    form = SearchForm()
    if request.method == 'GET':
        return render_template('search.html', form=form, AREAS=CONTENT['areas'])
    if request.method == 'POST':
        query = User.query  #pylint: disable=no-member

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
                User.projects]), ' ')).op('@@')(func.plainto_tsquery(form.fulltext.data)))

        # TODO ordering by relevance
        return render_template('search-results.html',
                               title='Expertise search',
                               form=form,
                               results=query.limit(20).all())


@views.route('/match')
@login_required
def match():
    '''
    Find innovators with answers
    '''
    if not current_user.skill_levels:
        flash(gettext('Before we can match you with fellow innovators, you need to '
                      'enter your expertise below first.'), 'error')
        return redirect(url_for('views.my_expertise'))
    return render_template('search-results.html',
                           title='People Who Know what I do not',
                           results=current_user.helpful_users)


@views.route('/match-knn')
@login_required
def knn():
    if 'user-expertise' not in session:
        flash('Before we can find innovators like you, you need to '
              '<a href="/my-expertise">fill your expertise</a> first.', 'error')
        return redirect(url_for('views.my_expertise'))
    query = {}
    if 'user-expertise' not in session:
        print "User expertise not in session"
        #my_needs = []
    else:
        skills = session['user-expertise']
    print skills
    experts = db.findMatchKnnAsJSON(skills)
    session['has_done_search'] = True
    return render_template('search-results.html',
                           **{'title': 'People most like me',
                              'results': experts, 'query': query})


@views.route('/users/recent')
def recent_users():
    users = User.query.order_by(desc(User.created_at)).limit(10).all()
    return render_template('search-results.html',
                           **{'title': 'Our Ten most recent members', 'results': users,
                              'query': ''})


@views.route('/feedback')
def feedback():
    return render_template('feedback.html', **{})


@views.route('/match-test')
def match_test():
    print session
    query = {'location': '', 'langs': [], 'skills': [], 'fulltext': 'NYU'}
    if 'user-expertise' not in session:
        session['user-expertise'] = {}
    experts = db.findMatchAsJSON(session['user-expertise'])
    return render_template('test.html',
                           **{'title': 'Matching search', 'results': experts, 'query': query})
