# app/checkin/views.py

from flask import flash, redirect, render_template, url_for, request, make_response, abort, jsonify
from flask_login import login_required, logout_user, current_user

from . import checkin_bp
from .forms import CheckForm
from ..models import PresenceList
from ..connectors import create_connectors, get_connector_by_id


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
                conn.checkin_field(info)
                flash('User {} Checked-IN!'.format(info))
            else:
                conn.checkout_field(info)
                flash('User {} Checked-OUT!'.format(info))
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

    # fetch statistics
    stats = conn.get_statistics()

    # fetch title and description
    evobj = conn.get_event()
    event_title = evobj['title']
    if 'time_start' in evobj:
        event_start = evobj['time_start'].strftime('%d.%m.%Y %H:%M')
    else:
        event_start = ""
    if 'description' in evobj:
        event_desc = evobj['description']
    else:
        event_desc = ""

    # load webpage
    return make_response(render_template('checkin/checkin.html',
                                         form=checkform,
                                         signups=signups,
                                         statistics=stats,
                                         event_title=event_title,
                                         event_start=event_start,
                                         event_desc=event_desc,
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

    # find appropriate connector
    conn = get_connector_by_id(create_connectors(), pl.conn_type)
    conn.token_login(pl.token)

    if pl.event_id is None:
        abort(make_response('No registered event for this PIN.', 400))

    # event is set, setup connector
    conn.set_event(pl.event_id)

    # get current signups
    try:
        signups = conn.get_signups_for_event()
    except Exception as E:
        abort(make_response('Error with API access: {:s}'.format(E), 502))

    # fetch statistics
    stats = conn.get_statistics()
    statsl = list()
    for k in stats:
        statsl.append({'key': k, 'value': stats[k]})

    j = {'signups': signups, 'statistics': statsl}
    return make_response(jsonify(j))
