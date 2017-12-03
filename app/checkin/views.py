# app/checkin/views.py

from flask import flash, redirect, render_template, url_for
from flask_login import login_required, login_user, logout_user, current_user

from . import checkin_bp
from .forms import CheckForm
from ..connectors import create_connectors, get_connector_by_id

@checkin_bp.route('/checkin')
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
    conn.set_token(pl.token)

    # if this pl has not set an event id yet, redirect to chooseevent
    if pl.event_id is None:
        return redirect(url_for('login.chooseevent'))

    # get current signups
    signups = conn.get_signups_for_event(pl.event_id)

    # load webpage
    checkform = CheckForm()
    return render_template('checkin/checkin.html', form=checkform, signups=signups, title='AMIV Check-In')

    