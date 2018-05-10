
from flask import redirect, render_template, url_for, abort, make_response, flash
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

        return redirect(url_for('checkin.checkin'))

    # load login template
    return make_response(render_template('gvtool/newgv.html',
                                         new_gv_form=new_gv_form,
                                         title='New GV'))
