# app/checkin/views.py

from flask import flash, redirect, render_template, url_for, request, make_response
from flask_login import login_required, logout_user, current_user

from . import checkin_bp
from .forms import CheckForm
from ..connectors import create_connectors, get_connector_by_id


@checkin_bp.route('/checkin', methods=['GET', 'POST'])
@login_required
def checkin():
    """
    Handle requests to the /register route
    Add an employee to the database through the registration form
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
    if request.method == 'POST':
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

    # load webpage
    return make_response(render_template('checkin/checkin.html',
                                         form=checkform,
                                         signups=signups,
                                         statistics=stats,
                                         title='AMIV Check-In'))
