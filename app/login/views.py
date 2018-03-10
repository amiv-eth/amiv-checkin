# app/login/views.py
from datetime import datetime

from flask import flash, redirect, render_template, url_for, request, abort, make_response
from flask_login import login_required, login_user, logout_user, current_user

from . import login_bp, generate_secure_pin
from .forms import PinLoginForm, CredentialsLoginForm
from .. import db
from ..models import PresenceList
from ..connectors import create_connectors, get_connector_by_id, gvtool_id_string
from ..security.security import register_failed_login_attempt, register_login_success


@login_bp.route('/')
def home():
    return redirect(url_for('login.login'))


@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle requests to the /login route
    """

    # check if user is logged in and redirect if necessary
    if current_user.is_authenticated:
        return redirect(url_for('checkin.checkin'))

    # create forms
    pinform = PinLoginForm()
    credform = CredentialsLoginForm()
    connectors = create_connectors()

    # fill form with connectors
    conn_select = []
    for c in connectors:
        conn_select.append((c.id_string, c.human_string))
    credform.backend.choices = conn_select

    if request.method == 'POST':
        if 'method_PIN' in request.values:
            if pinform.validate_on_submit():
                
                # PIN form was submitted, try user login
                inputpin = pinform.pin.data

                # get all presence lists with given PIN
                presencelists = PresenceList.query.filter_by(pin=inputpin).all()
                
                if len(presencelists) > 1:
                    # we have a database error
                    raise Exception('Multiple PresenceList with same PIN found!')

                if len(presencelists) > 0:
                    pl = presencelists[0]
                    if pl.pin == inputpin:
                        login_user(pl)
                        register_login_success()
                        return redirect(url_for('checkin.checkin'))

                register_failed_login_attempt()
                flash('Invalid PIN.', 'error')
                    
        elif 'method_Cred' in request.values:
            if credform.validate_on_submit():

                # credential form was submitted, check connector type
                conn = get_connector_by_id(connectors, credform.backend.data)

                # try to validate against connector
                un = credform.username.data
                pw = credform.password.data
                try: 
                    token = conn.login(un, pw)
                except Exception as E:
                    register_failed_login_attempt()
                    flash(str(E), 'error')
                    return redirect(url_for('login.login'))

                # credentials are valid
                register_login_success()

                # create new user! Create new pin and check if already set.
                retrycnt = 1000
                while retrycnt > 0:
                    # create secure new random pin
                    pin = generate_secure_pin()
                    if len(PresenceList.query.filter_by(pin=pin).all()) == 0:
                        break
                    retrycnt = retrycnt-1
                if retrycnt == 0:
                    print("Could not find a free pin! Delete some PresenceList from DB!")
                    abort(500)

                # create new user account
                npl = PresenceList(conn_type=conn.id_string, pin=pin, token=token, event_id=None)
                db.session.add(npl)
                db.session.commit()
                login_user(npl)
                return redirect(url_for('login.chooseevent'))
                    
        else:
            print('Did not find correct hidden value in POST request.')
            abort(400)

    # load login template
    return make_response(render_template('login/login.html', pinform=pinform, credform=credform, title='Login'))


def beautify_event(raw_event, additional_fields={}):
    """
    Beautify event dict to include strings for display.
    :param raw_event: dict as returned by conn.get_event()
    :param additional_fields: dict which just gets all the keys copied to the output
    :return: dict with signup_string and time_string added
    """
    if 'signup_count' in raw_event:
        spots = 'unlimited' if raw_event['spots'] == 0 else raw_event['spots']
        raw_event['signups_string'] = "{} / {}".format(raw_event['signup_count'], spots)
    if 'time_start' in raw_event:
        raw_event['time_string'] = raw_event['time_start'].strftime('%d.%m.%Y %H:%M')
    for k in additional_fields:
        raw_event[k] = additional_fields[k]
    return raw_event


@login_bp.route('/chooseevent', methods=['GET', 'POST'])
@login_required
def chooseevent():
    """
    Handle requests to the /chooseevent route
    """

    # get connector
    connectors = create_connectors()
    pl = current_user
    conn = get_connector_by_id(connectors, pl.conn_type)
    conn.token_login(pl.token)

    # catch case where event_id is already assigned
    if pl.event_id is not None:
        abort(403)

    # gather possible events in this list
    upcoming_events = []

    # get all already tracked events
    not_found_events = []  # save event ids of events which the API fails to GET
    found_events = []
    # query all presence lists for current event type
    existing_pls = PresenceList.query\
        .filter(PresenceList.conn_type == conn.id_string)\
        .filter(PresenceList.event_id >= 0)\
        .all()
    for pl in existing_pls:
        # retreive event information from data source
        conn.set_event(pl.event_id)
        try:
            evobj = conn.get_event()
        except Exception as E:
            not_found_events.append(str(pl.event_id))
            continue
        # we found a tracked event, add it to the list
        found_events.append(pl.event_id)
        upcoming_events.append(beautify_event(evobj, {'event_ended': pl.event_ended}))

    # get upcoming events
    try:
        events = conn.get_next_events()
    except Exception as E:
        flash("Could not get next events: {}".format(E), 'error')
        return logout_and_delete_pin()
    for e in events:
        if e['_id'] not in found_events:
            upcoming_events.append(beautify_event(e, {'event_ended': False}))

    if len(not_found_events) > 0:
        flash('Warning: The following event IDs do '
              'not seem to exist in the chosen '
              'data source: {:s}.'.format(', '.join(not_found_events))
              , 'warning')

    # sort the list by start date (newest first)
    upcoming_events = sorted(upcoming_events,
                             key=lambda k: k['time_start'] if ('time_start' in k) else datetime(1970, 1, 1),
                             reverse=True)

    # check if we are running on GVs:
    if conn.id_string == gvtool_id_string:
        # when using the GV tool connector,
        # we allow the user to create a new gv
        show_new = True
    else:
        show_new = False

    # on GET, render page
    return make_response(render_template('login/chooseevent.html',
                                         title='Choose Event',
                                         upcoming_events=upcoming_events,
                                         allow_create_new=show_new
                                         ))


@login_bp.route('/chooseevent/select/<string:_id>')
@login_required
def select_chooseevent(_id):

    # get connector
    connectors = create_connectors()
    pl = current_user
    conn = get_connector_by_id(connectors, pl.conn_type)
    conn.token_login(pl.token)

    # catch case where event_id is already assigned
    if pl.event_id is not None:
        abort(403)

    # check if event ID exists:
    conn.set_event(_id)
    try:
        evobj = conn.get_event()
    except Exception as E:
        flash("Invalid event ID selected: {:s}".format(E), 'error')
        return logout_and_delete_pin()

    # check if user already exists for event id
    existing_pls = PresenceList.query.filter_by(conn_type=pl.conn_type, event_id=evobj['_id']).all()
    if len(existing_pls) > 1:
        flash('More than one tracking list found for given event. Internal DB Error.', 'error')
        logout_user()
        return redirect(url_for('login.login'))
    elif len(existing_pls) == 1:
        # we have already a pin registered for this event, open event, renew token,
        # show old pin, logout user, and redirect
        existing_pl = existing_pls[0]
        existing_pl.token = pl.token
        existing_pl.event_ended = False
        pin_to_remove = pl.pin
        existing_pin = existing_pls[0].pin
        logout_user()
        # delete just created PresenceList from database as it now will not be used
        new_pl = PresenceList.query.filter_by(pin=pin_to_remove).one()
        db.session.delete(new_pl)
        db.session.commit()
        flash('PIN already exists for this event! Use PIN {} to login.'.format(existing_pin))
        return redirect(url_for('login.login'))

    # ok, new event chosen. Set event_id in current PresenceList and go further
    pl.event_id = evobj['_id']
    db.session.commit()
    return redirect(url_for('checkin.checkin'))


@login_bp.route('/logout')
@login_required
def logout():
    """
    Handle requests to the /logout route
    """
    logout_user()
    flash('You have successfully been logged out.')

    # redirect to the login page
    return redirect(url_for('login.login'))


@login_bp.route('/logout_and_delete_pin')
@login_required
def logout_and_delete_pin():
    """
    Handle requests to the /logout_and_delete_pin route
    """
    s = PresenceList.query.filter_by(pin=current_user.pin).all()
    if len(s) > 0:
        # only allow pin deletion if no event is assigned yet
        pl = s[0]
        if pl.event_id is not None:
            abort(403)
        # save pin and logout user
        pin_to_remove = current_user.pin
        logout_user()
        # delete wrongly created PresenceList from database
        s = PresenceList.query.filter_by(pin=pin_to_remove).one()
        db.session.delete(s)
        db.session.commit()
    else:
        # should never happen
        logout_user()

    # redirect to the login page
    return redirect(url_for('login.login'))


@login_bp.route('/privacy')
def privacy():
    """
    Display the privacy statement.
    """
    return render_template('login/privacy.html')
