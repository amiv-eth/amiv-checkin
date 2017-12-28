# app/checkin/views.py

from flask import flash, redirect, render_template, url_for, request, make_response, abort, jsonify
from flask_login import login_required, logout_user, current_user

from . import checkin_bp
from .forms import CheckForm
from .. import db
from ..login import generate_secure_pin
from ..models import PresenceList
from ..connectors import create_connectors, get_connector_by_id, gvtool_id_string


@checkin_bp.route('/checkin', methods=['GET', 'POST'])
@login_required
def checkin():
    """
    Main Webpage for all the signups. Also takes requests
    from the manual check-in / check-out form.
    """

    # get connector
    connectors = create_connectors()
    pl = current_user
    conn = get_connector_by_id(connectors, pl.conn_type)
    conn.token_login(pl.token)

    # if this pl has not set an event id yet, redirect to chooseevent
    if pl.event_id is None:
        return redirect(url_for('login.chooseevent'))

    # event is set, setup connector
    conn.set_event(pl.event_id)

    # create form
    checkform = CheckForm()

    # check form submission
    if checkform.validate_on_submit():
        checkmode = checkform.checkmode.data
        info = checkform.datainput.data

        try:
            if checkmode == 'in':
                su = conn.checkin_field(info)
                flash('{:s} member {:s} checked-IN!'.format(su['membership'].upper(), info))
            else:
                su = conn.checkout_field(info)
                flash('{:s} member {:s} checked-OUT!'.format(su['membership'].upper(), info))
        except Exception as E:
            flash('Error: '+str(E), 'error')

    # get current signups
    try:
        signups = conn.get_signups_for_event()
    except Exception as E:
        flash('Could not get signups for event: {}'.format(str(E)), 'error')
        logout_user()
        return redirect(url_for('login.login'))

    # output values
    for s in signups:
        # signups is boolean, make it human readable
        if s['checked_in'] is None:
            s['checked_in'] = '-'
        elif s['checked_in']:
            s['checked_in'] = 'IN'
        else:
            s['checked_in'] = 'OUT'
        # legi could be None
        if s['legi'] is None:
            s['legi'] = 'unknown'
        # capitalize first letter in membership
        s['membership'] = s['membership'][0].upper() + s['membership'][1:]

    # fetch statistics
    stats = conn.get_statistics()

    # fetch title and description
    evobj = conn.get_event()
    event_title = evobj['title']
    if 'time_start' in evobj:
        event_start = evobj['time_start'].strftime('%d.%m.%Y %H:%M')
    else:
        event_start = ""

    # enable button for log download if we are in GV mode
    if conn.id_string == gvtool_id_string:
        show_log_btn = True
    else:
        show_log_btn = False

    # load webpage
    return make_response(render_template('checkin/checkin.html',
                                         form=checkform,
                                         signups=signups,
                                         statistics=stats,
                                         event_title=event_title,
                                         event_start=event_start,
                                         log_download=show_log_btn,
                                         title='AMIV Check-In'))


@checkin_bp.route('/checkin_update_data')
def checkin_update_data():
    """
    Delivers the table contents on the webpage.
    """

    # check if pin is supplied
    pin = request.headers.get('pin')
    if pin is None:
        # if no pin is supplied, check if we are logged in
        if not current_user.is_authenticated:
            abort(make_response('Not logged in.', 401))
        pl = current_user
    else:
        # pin supplied, find current user via database
        pls = PresenceList.query.filter_by(pin=pin).all()
        if len(pls) != 1:
            abort(make_response('PIN invalid.', 401))
        else:
            pl = pls[0]

    if pl.event_id is None:
        abort(make_response('No registered event for this PIN.', 400))

    # find appropriate connector
    conn = get_connector_by_id(create_connectors(), pl.conn_type)
    conn.token_login(pl.token)

    # event is set, setup connector
    conn.set_event(pl.event_id)

    # get current signups
    try:
        signups = conn.get_signups_for_event()
    except Exception as E:
        abort(make_response('Error with API access: {:s}'.format(str(E)), 502))

    # fetch statistics
    stats = conn.get_statistics()
    statsl = list()
    for k in stats:
        statsl.append({'key': k, 'value': stats[k]})

    j = {'signups': signups, 'statistics': statsl}
    return make_response(jsonify(j))


@checkin_bp.route('/change_pin')
@login_required
def change_pin():
    """
    Generates a new pin for the user and logs the user out.
    """

    # create new pin and check if already occupied
    retrycnt = 1000
    while retrycnt > 0:
        # create secure new random pin
        newpin = generate_secure_pin()
        if PresenceList.query.filter_by(pin=newpin).count() == 0:
            break
        retrycnt = retrycnt - 1
    if retrycnt == 0:
        print("Could not find a free pin! Delete some PresenceList from DB!")
        abort(500)

    # logout user and change pin
    pin_to_change = current_user.pin
    logout_user()
    pl = PresenceList.query.filter_by(pin=pin_to_change).one()
    pl.pin = newpin
    db.session.commit()

    # inform user and redirect
    flash('PIN changed! Use new PIN {} to login.'.format(newpin))
    return redirect(url_for('login.login'))
