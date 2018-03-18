# app/event/views.py
from datetime import datetime
import collections
from flask import (flash, abort, make_response, render_template,
                   redirect, url_for)
from flask_login import login_required, current_user

from ..connectors import Event_Interface, gvtool_id_string
from ..models import PresenceList
from ..login.logic import beautify_event, logout_and_delete_pin
from .. import db
from . import event_bp
from .forms import EventTypeForm


@event_bp.route('/choosetheevent', methods=['GET', 'POST'])
@login_required
def choosetheevent():
    """
    Handle requests to the /choosetheevent route
    """

    # get connector
    pl = current_user
    conn = Event_Interface()
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
        .filter(PresenceList.event_id >= 0)\
        .filter(PresenceList.conn_type != gvtool_id_string)\
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
        upcoming_events.append(beautify_event(evobj, {'event_ended': pl.event_ended, 'has_PIN': True, 'PIN':pl.pin}))

    # get upcoming events
    try:
        events = conn.get_next_events()
    except Exception as E:
        flash("Could not get next events: {}".format(E), 'error')
        return logout_and_delete_pin()
    for e in events:
        if e['_id'] not in found_events:
            upcoming_events.append(beautify_event(e, {'event_ended': False, 'has_PIN' : False }))

    if len(not_found_events) > 0:
        flash('Warning: The following event IDs do '
              'not seem to exist in the chosen '
              'data source: {:s}.'.format(', '.join(not_found_events))
              , 'warning')

    # sort the list by start date (newest first)
    upcoming_events = sorted(upcoming_events,
                             key=lambda k: k['time_start'] if ('time_start' in k) else datetime(1970, 1, 1),
                             reverse=True)

    # on GET, render page
    return make_response(render_template('event/choosetheevent.html',
                                         title='Choose Event',
                                         upcoming_events=upcoming_events))


@event_bp.route('/setupevent/<string:_id>', methods=['GET', 'POST'])
@login_required
def setupevent(_id):
    """
    Handle requests to the /choosetheevent route
    """

    pl = current_user
    conn = Event_Interface()
    conn.token_login(pl.token)
    conn.set_event(_id)
    try:
        evobj = conn.get_event()
    except Exception as E:
        flash("Could not get event: {}".format(_id), 'error')
        return logout_and_delete_pin()

    event_data = beautify_event(evobj)
    event_data_to_show = {k: event_data[k] for k in event_data if k in ['title', 'catchphrase_en', 'description_en', 'price', 'time_start', 'time_end', 'spots', 'allow_email_signup', 'signup_count', 'signups_string']}
    event_data_to_show = collections.OrderedDict(sorted(event_data_to_show.items()))

    event_type_form = EventTypeForm()

    if event_type_form.validate_on_submit():
        event_type = event_type_form.eventtype.data
        maxcount = event_type_form.maxcounter.data

        if event_type == 'counter' and maxcount is None:
            maxcount = 1

        return process_event_setup(_id, event_type, maxcount)

    return make_response(render_template('event/event_setup.html',
                                         title='Setup Event',
                                         event_data=event_data_to_show,
                                         form=event_type_form))


@login_required
def process_event_setup(_id, event_type, maxcount):

    pl = current_user

    pl.event_type = event_type

    if event_type == 'counter':
        pl.event_max_counter = maxcount

    pl.event_id = _id
    db.session.commit()

    return redirect(url_for('checkin.checkin', _event_type=event_type))
