# app/checkin/views.py

from flask import request, abort, make_response

from . import mutate_bp
from ..models import PresenceList
from ..connectors import create_connectors, get_connector_by_id


@mutate_bp.route('/mutate', methods=['POST'])
def mutate():
    """
    check-in or check-out people without login but with pin
    """

    # parse and validate request data

    try:
        pin = int(request.form['pin'])
        checkmode = str(request.form['checkmode']).strip().lower()
        if checkmode != 'in' and checkmode != 'out':
            raise Exception('invalid checkmode: {}'.format(checkmode))
        info = str(request.form['info'])
    except Exception as E:
        print(E)
        abort(make_response('Malformed request. ({})'.format(str(E)), 400))

    # find PresenceList with pin
    pls = PresenceList.query.filter_by(pin=pin).all()
    if len(pls) != 1:
        abort(make_response('PIN invalid.', 401))
    else:
        pl = pls[0]

    # get correct connector, login, and set respective event
    connectors = create_connectors()
    conn = get_connector_by_id(connectors, pl.conn_type)
    conn.token_login(pl.token)
    conn.set_event(pl.event_id)

    # check-in/-out user
    try:
        if checkmode == 'in':
            conn.checkin_field(info)
            return make_response('Checked-IN!', 200)
        else:
            conn.checkout_field(info)
            return make_response('Checked-OUT!', 200)
    except Exception as E:
        print(E)
        abort(make_response(str(E), 400))


@mutate_bp.route('/checkpin', methods=['POST'])
def checkpin():
    """
    check if a given pin is valid
    """

    # parse and validate request data
    try:
        pin = int(request.form['pin'])
    except Exception as E:
        print(E)
        abort(make_response('Malformed request.', 400))

    # find PresenceList with given pin
    pls = PresenceList.query.filter_by(pin=pin).all()
    if len(pls) != 1:
        abort(make_response('PIN invalid.', 403))
    else:
        return make_response('PIN valid.', 200)
    

