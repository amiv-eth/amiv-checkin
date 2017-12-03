# app/checkin/views.py

from flask import flash, redirect, render_template, url_for, request
from flask_login import login_required, login_user, logout_user, current_user

from . import checkin_bp
from .forms import CheckForm
from ..connectors import create_connectors, get_connector_by_id

@checkin_bp.route('/checkin', methods=['GET','POST'])
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


    # create form (do POST check here)
    checkform = CheckForm()
    if request.method == 'POST':
        if checkform.validate_on_submit():
            checkmode = checkform.checkmode.data
            info = checkform.datainput.data

            try:
                if checkmode == 'in':
                    conn.checkin_field(info)
                    flash('Checked-IN!')
                else:
                    conn.checkout_field(info)
                    flash('Checked-OUT!')
            except Exception as E:
                flash('Error: '+str(E))

    # get current signups
    signups = conn.get_signups_for_event()

    # translate signups boolean to human readable info
    for s in signups:
        if s['checked_in'] is None:
            s['checked_in'] = '-'
        elif s['checked_in']:
            s['checked_in'] = 'IN'
        else:
            s['checked_in'] = 'OUT'

    # load webpage
    return render_template('checkin/checkin.html', form=checkform, signups=signups, title='AMIV Check-In')
