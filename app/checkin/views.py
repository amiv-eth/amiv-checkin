# app/checkin/views.py

from flask import flash, redirect, render_template, url_for, request, make_response, abort, jsonify, Response
from flask_login import login_required, logout_user, current_user
import csv
import datetime
from io import StringIO

from . import checkin_bp
from .forms import CheckForm, CSRFCheckForm
from .. import db
from ..login import generate_secure_pin
from ..models import PresenceList
from ..connectors import create_connectors, get_connector_by_id
from ..security.security import register_failed_login_attempt, register_login_success


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
            if pl.event_ended:
                raise Exception('Event ended. No changes allowed.')
            if checkmode == 'in':
                rd = conn.checkin_field(info)
                flash(rd['message'])
            else:
                rd = conn.checkout_field(info)
                flash(rd['message'])
        except Exception as E:
            flash('Error: ' + str(E), 'error')

    # fetch title and description
    try:
        evobj = conn.get_event()
        event_title = evobj['title']
        if 'time_start' in evobj:
            event_start = evobj['time_start'].strftime('%d.%m.%Y %H:%M')
        else:
            event_start = ""
    except Exception as E:
        flash('Error: ' + str(E), 'error')
        event_title = "< unknown >"
        event_start = ""

    # enable button for log download if the current connector offers a get_log() function
    # to allow the user to download the .csv log
    if "get_log" in dir(conn):
        show_log_btn = True
    else:
        show_log_btn = False

    # load webpage
    return make_response(render_template('checkin/checkin.html',
                                         form=checkform,
                                         event_ended=pl.event_ended,
                                         event_title=event_title,
                                         event_start=event_start,
                                         log_download=show_log_btn,
                                         csrfcheckform=CSRFCheckForm(),
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
            register_failed_login_attempt()
            abort(make_response('PIN invalid.', 401))
        else:
            register_login_success()
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
    try:
        stats = conn.get_statistics()
    except Exception as E:
        abort(make_response('Error with API access: {:s}'.format(str(E)), 502))
    statsl = list()
    for k in stats:
        statsl.append({'key': k, 'value': stats[k]})

    # fetch information about event
    try:
        evobj = conn.get_event()
    except Exception as E:
        abort(make_response('Error with API access: {:s}'.format(str(E)), 502))
    evobj['event_type'] = conn.human_string  # add description of event type

    j = {'signups': signups, 'statistics': statsl, 'eventinfos': evobj}
    return make_response(jsonify(j))


@checkin_bp.route('/change_pin', methods=['POST'])
@login_required
def change_pin():
    """
    Generates a new pin for the user and logs the user out.
    """

    # do CSRF check on POST data
    cpform = CSRFCheckForm()
    if not cpform.validate():
        abort(make_response('CSRF check failed.', 400))

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


@checkin_bp.route('/close_event', methods=['POST'])
@login_required
def close_event():
    """
    Closes the event.
    """

    # do CSRF check on POST data
    cpform = CSRFCheckForm()
    if not cpform.validate():
        abort(make_response('CSRF check failed.', 400))

    # check if already closed
    pl = current_user
    if pl.event_ended:
        abort(make_response('Event already closed.', 400))

    # setup connector
    conn = get_connector_by_id(create_connectors(), pl.conn_type)
    conn.token_login(pl.token)
    conn.set_event(pl.event_id)

    try:
        # checkout all checked-in users
        conn.checkout_all_remaining()
    except Exception as E:
        flash('Error: ' + str(E), 'error')
        return redirect(url_for('checkin.checkin'))

    # mark event as ended
    pl.event_ended = True
    db.session.commit()

    # inform user and redirect
    flash('Event closed.')
    return redirect(url_for('checkin.checkin'))


@checkin_bp.route('/export_csv')
@login_required
def export_csv():
    """
    Let the user download a CSV file with all user check-in and check-out timestamps
    """

    # get connector
    connectors = create_connectors()
    pl = current_user
    conn = get_connector_by_id(connectors, pl.conn_type)
    conn.token_login(pl.token)

    # catch if user did not choose an appropriate backend for log exprting
    if "get_log" not in dir(conn):
        abort(make_response('Cannot export CSV for a backend not providing get_log() function.', 403))

    # catch case if the event is not chosen yet
    if pl.event_id is None:
        abort(make_response('Cannot export CSV for PresenceList with no assigned event ID.', 403))

    # retrieve list of cleaned log entries
    conn.set_event(pl.event_id)
    try:
        event_reference = conn.get_event()
        loglist = conn.get_log()
    except Exception as E:
        abort(make_response('Error with API access: {:s}'.format(str(E)), 502))

    # assemble csv output file
    outcsv = StringIO()  # creates a memory-mapped file structure
    nlchar = '\r\n'

    # header
    outcsv.write('// AMIV Checkin Log File' + nlchar)
    outcsv.write('// {:s}'.format(event_reference['title']) + nlchar)
    if 'time_start' in event_reference:
        outcsv.write('// {:s}'.format(event_reference['time_start'].strftime('%d.%m.%Y %H:%M')) + nlchar)
    if 'description' in event_reference:
        desc = event_reference['description'].replace('\n', '\n// ')
        outcsv.write('// {:s}'.format(desc) + nlchar)
    if len(loglist) > 0:
        outcsv.write('// Columns: ' + ', '.join(['"' + str(k) + '"' for k, _ in loglist[0].items()]) + nlchar)

    # add log data
    csvwriter = csv.writer(outcsv, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    for log in loglist:
        csvwriter.writerow([v for _, v in log.items()])

    # create filename
    fn = 'AMIV_Checkin_Log_{:s}'.format(str(int(datetime.datetime.now().timestamp())))

    # return response (this results in a download file dialog in most browsers)
    return Response(
        outcsv.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename={:s}.csv".format(fn)})
