
from flask import flash, redirect, render_template, url_for, request, abort, make_response
from flask_login import login_required, login_user, logout_user, current_user

from . import gvtool_bp
from .forms import CreateNewGVForm
from .. import db
from ..connectors import create_connectors, get_connector_by_id
from ..connectors.gvtool_models import GVEvent


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

    # create form
    new_gv_form = CreateNewGVForm()

    if new_gv_form.validate_on_submit():
        # create new gv event
        title = new_gv_form.title.data
        desc = new_gv_form.description.data
        gv = conn.create_new_gv(title, desc)

        # attach event to current user
        pl.event_id = gv._id
        db.session.commit()

        return redirect(url_for('checkin.checkin'))

    # load login template
    return make_response(render_template('gvtool/newgv.html',
                                         new_gv_form=new_gv_form,
                                         title='New GV'))