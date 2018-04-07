import csv
import datetime
from io import StringIO
from flask import redirect, render_template, url_for, abort, make_response, Response, flash
from flask_login import login_required, current_user

from . import freebies_bp
from .forms import CreateNewFreebieEvent
from .. import db
from ..connectors import create_connectors, get_connector_by_id, freebies_id_string


@freebies_bp.route('/new_freebie', methods=['GET', 'POST'])
@login_required
def new_freebie():
    """
    Handle requests to the /new_freebie route
    """

    # get connector
    connectors = create_connectors()
    pl = current_user
    conn = get_connector_by_id(connectors, pl.conn_type)
    conn.token_login(pl.token)

    # catch if user did not choose the freebie tool as backend:
    if pl.conn_type != freebies_id_string:
        abort(make_response('Cannot create new Freebie Tracker for non-Freebie PresenceList.', 403))

    # catch case where there is already an event chosen
    if pl.event_id is not None:
        abort(make_response('Cannot create new Freebie Tracker for PresenceList with already assigned ID.', 403))

    # create form
    new_form = CreateNewFreebieEvent()

    if new_form.validate_on_submit():
        # create new gv event
        title = new_form.title.data
        desc = new_form.description.data
        Nmax = new_form.max_freebies.data
        try:
            fbt = conn.create_new_freebie_tracker(title, desc, Nmax)
        except Exception as E:
            flash('Error: ' + str(E), 'error')
            return redirect(url_for('freebies.new_freebie'))

        # attach event to current user
        pl.event_id = fbt._id
        db.session.commit()

        return redirect(url_for('checkin.checkin'))

    # load login template
    return make_response(render_template('freebies/newfreebietracker.html',
                                         new_form=new_form,
                                         title='New Freebie Tracking'))
