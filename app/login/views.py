# app/login/views.py

from flask import flash, redirect, render_template, url_for, request, abort
from flask_login import login_required, login_user, logout_user, current_user
import secrets

from . import login_bp
from .forms import PinLoginForm, CredentialsLoginForm, ChooseEventForm
from .. import db
from ..models import PresenceList
from ..connectors import create_connectors, get_connector_by_id

@login_bp.route('/')
def home():
    return redirect(url_for('login.login'))


@login_bp.route('/login', methods=['GET','POST'])
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
        conn_select.append( (c.id_string,c.human_string) )
    credform.backend.choices = conn_select

    if request.method == 'POST':
        if 'method_PIN' in request.values:
            if pinform.validate_on_submit():
                
                # PIN form was submitted, try user login
                
                inputpin = pinform.pin.data
                print("entered pin: {}".format(inputpin))

                # get all presence lists with given PIN
                presencelists = PresenceList.query.filter_by(pin=inputpin).all()
                print("presencelists length: {}".format(len(presencelists)))
                
                if len(presencelists) > 1:
                    # we have a database error
                    raise Error('Multiple PresenceList with same PIN found!')

                if len(presencelists) > 0:
                    pl = presencelists[0]
                    if pl.pin == inputpin:
                        login_user(pl)
                        return redirect(url_for('checkin.checkin'))

                flash('Invalid PIN.')
                
                    
        elif 'method_Cred' in request.values:
            if credform.validate_on_submit():

                # credential form was submitted, check connector type
                try:
                    conn = get_connector_by_id(connectors, credform.backend.data)
                except Exception as E:
                    print(E)
                    abort(400)

                # try to validate against connector
                un = credform.username.data
                pw = credform.password.data
                token = conn.login(un, pw)
                if token is None:
                    flash('Invalid username or password.')
                    return redirect(url_for('login.login'))

                # credentials are valid, create new user! Create new pin and check if already set.
                retrycnt = 1000;
                while retrycnt > 0:
                    # create secure new random pin
                    pin = 100000 + secrets.randbelow(900000)
                    if len(PresenceList.query.filter_by(pin=pin).all()) == 0:
                        break
                    retrycnt = retrycnt-1
                if retrycnt == 0:
                    print("Could not find a free pin! Delete some PresenceList from DB!")
                    abort(500)

                # create new user account
                npl = PresenceList(conn_type=conn.id_string, pin=pin, token=token, event_id="--none--")
                db.session.add(npl)
                db.session.commit()
                login_user(npl)
                return redirect(url_for('login.chooseevent'))
                    
        else:
            print('Did not find correct hidden value in POST request.')
            abort(500)

    # load login template
    return render_template('login/login.html', pinform=pinform, credform=credform, title='Login')


@login_bp.route('/chooseevent', methods=['GET','POST'])
@login_required
def chooseevent():
    """
    Handle requests to the /chooseevent route
    """

    # get connector
    connectors = create_connectors()
    pl = current_user
    conn = get_connector_by_id(connectors, pl.conn_type)

    # create form
    chooseeventform = ChooseEventForm()
    try:
        events = conn.get_next_events(pl.token);
    except:
        print("Could not get next events.")
        print(E)
        abort(500)

    # create event list for drop-down menu
    elist = []
    for e in events:
        elist.append((e['id'], e['title']))
    chooseeventform.chooseevent.choices = elist

    # check if we are on POST
    if request.method == 'POST':
        if chooseeventform.validate_on_submit():
            # get event id string and find the corresponding event object
            ev_id_string = chooseeventform.chooseevent.data
            ev = None
            for eidx in range(len(events)):
                if events[eidx]['id'] == ev_id_string:
                    ev = events[eidx]
                    break
            if ev is None:
                # user submitted non-existing event id
                abort(400)

            # check if user already exists for event id
            print(pl.conn_type)
            print(ev['id'])
            s = PresenceList.query.filter_by(conn_type=pl.conn_type, event_id=ev['id']).all()
            print(s)
            if len(s) > 0:
                # we have already a pin registered for this event, renew token, show old pin, logout user, and redirect
                s[0].token = pl.token
                pin_to_remove = pl.pin
                existing_pin = s[0].pin
                logout_user()
                # delete wrongly created PresenceList from database
                s = PresenceList.query.filter_by(pin=pin_to_remove).one()
                db.session.delete(s)
                db.session.commit()
                flash('PIN already exists for this event! Use PIN {} to login.'.format(existing_pin))
                return redirect(url_for('login.login'))

            # ok, new event chosen. Set event_id in current PresenceList and go further
            pl.event_id = ev['id']
            db.session.commit()
            return redirect(url_for('checkin.checkin'))

    # on GET, render page
    return render_template('login/chooseevent.html', form=chooseeventform, title='Choose Event')


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
