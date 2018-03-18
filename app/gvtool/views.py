import csv
import datetime
from io import StringIO
from flask import redirect, render_template, url_for, abort, make_response, Response, flash
from flask_login import login_required, current_user

from . import gvtool_bp
from .forms import CreateNewGVForm
from .. import db
from ..connectors import create_connectors, get_connector_by_id, gvtool_id_string


@gvtool_bp.route('/new_gv', methods=['GET', 'POST'])
@login_required
def new_gv():
    """
    Handle requests to the /new_gv route
    """

    # get connector
    connectors = create_connectors()
    pl = current_user
    conn = get_connector_by_id(connectors, pl.conn_type)
    conn.token_login(pl.token)

    # catch if user did not choose the GV tool as backend:
    if pl.conn_type != gvtool_id_string:
        abort(make_response('Cannot create new GV for non-GV PresenceList.', 403))

    # catch case where there is already an event chosen
    if pl.event_id is not None:
        abort(make_response('Cannot create new GV for PresenceList with already assigned ID.', 403))

    # create form
    new_gv_form = CreateNewGVForm()

    if new_gv_form.validate_on_submit():
        # create new gv event
        title = new_gv_form.title.data
        desc = new_gv_form.description.data
        try:
            gv = conn.create_new_gv(title, desc)
        except Exception as E:
            flash('Error: ' + str(E), 'error')
            return redirect(url_for('gvtool.new_gv'))

        # attach event to current user
        pl.event_id = gv._id
        db.session.commit()

        return redirect(url_for('checkin.checkin', _event_type='in_out'))

    # load login template
    return make_response(render_template('gvtool/newgv.html',
                                         new_gv_form=new_gv_form,
                                         title='New GV'))


@gvtool_bp.route('/export_csv')
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

    # catch if user did not choose the GV tool as backend
    if pl.conn_type != gvtool_id_string:
        abort(make_response('Cannot export CSV for non-GV PresenceList.', 403))

    # catch case if the event is not chosen yet
    if pl.event_id is None:
        abort(make_response('Cannot export CSV for PresenceList with no assigned ID.', 403))

    # retrieve list of cleaned log entries
    conn.set_event(pl.event_id)
    try:
        gv = conn.get_event()
        loglist = conn.get_gv_attendance_log()
    except Exception as E:
        abort(make_response('Error with API access: {:s}'.format(str(E)), 502))

    # assemble csv output file
    outcsv = StringIO()  # creates a memory-mapped file structure
    nlchar = '\r\n'

    # header
    outcsv.write('// Attendance Log' + nlchar)
    outcsv.write('// {:s}'.format(gv['title']) + nlchar)
    if 'time_start' in gv:
        outcsv.write('// {:s}'.format(gv['time_start'].strftime('%d.%m.%Y %H:%M')) + nlchar)
    if 'description' in gv:
        desc = gv['description'].replace('\n', '\n// ')
        outcsv.write('// {:s}'.format(desc) + nlchar)
    if len(loglist) > 0:
        outcsv.write('// Columns: ' + ', '.join(['"'+str(k)+'"' for k, _ in loglist[0].items()]) + nlchar)

    # add log data
    csvwriter = csv.writer(outcsv, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    for log in loglist:
        csvwriter.writerow([v for _, v in log.items()])

    # create filename
    fn = 'Attendance_Log_{:s}'.format(str(int(datetime.datetime.now().timestamp())))

    # return response
    return Response(
        outcsv.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename={:s}.csv".format(fn)})
