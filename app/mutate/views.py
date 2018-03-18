# app/checkin/views.py

from flask import request, abort, make_response, jsonify

from . import mutate_bp
from ..models import PresenceList
from ..connectors import create_connectors, get_connector_by_id
from ..security.security import register_failed_login_attempt, register_login_success
from ..checkin.views import is_signup_needed

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
        abort(make_response('Malformed request {}. ({})'.format(request.form, str(E)), 400))

    # find PresenceList with pin
    pls = PresenceList.query.filter_by(pin=pin).all()
    if len(pls) != 1:
        register_failed_login_attempt()
        abort(make_response('PIN invalid.', 401))
    else:
        register_login_success()
        pl = pls[0]

    # check if event is closed:
    if pl.event_ended:
        abort(make_response('Event ended. No changes allowed.', 400))

    # get correct connector, login, and set respective event
    connectors = create_connectors()
    conn = get_connector_by_id(connectors, pl.conn_type)
    conn.token_login(pl.token)
    conn.set_event(pl.event_id)

    if pl.event_type == 'in_out':
        # check-in/-out user
        try:
            if checkmode == 'in':
                su = conn.checkin_field(info)
                rd = {'message': '{:s} member checked-IN!'.format(su['membership'].upper()), 'signup': su}
                return make_response(jsonify(rd), 200)
            else:
                su = conn.checkout_field(info)
                rd = {'message': '{:s} member checked-OUT!'.format(su['membership'].upper()), 'signup': su}
                return make_response(jsonify(rd), 200)
        except Exception as E:
            abort(make_response(str(E), 400))
    elif pl.event_type == 'counter':
        if checkmode == 'in':
            try:
                evobj = conn.get_event()
                signup_needed = is_signup_needed(evobj)
                count = conn.count_increment(info, signup_needed, pl.event_max_counter)
                user_id = conn._get_userinfo_from_info(info)['_id']
                r = conn._api_get('/users?where={"_id":"%s"}' % user_id)
                r = r.json()['_items'][0]
                r = {'firstname': r['firstname'],
                     'lastname': r['lastname'],
                     'nethz': r['nethz'],
                     'email': r['email'],
                     'legi': r['legi'],
                     'membership': r['membership'],
                     'user_id': user_id,
                     'count': count}

                rd = {'message': '{:s} member counted {}!'.format(info, count),
                      'signup': r}
                return make_response(jsonify(rd), 200)

            except Exception as E:
                abort(make_response(str(E), 400))
        else:
            abort(make_response(
                'Checkmode {} invalid for this event type {} invalid.'.format(
                    checkmode, pl.event_type), 400))
    else:
        abort(make_response('Event type {} invalid.'.format(pl.event_type), 400))


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
        register_failed_login_attempt()
        abort(make_response('PIN invalid.', 401))
    else:
        register_login_success()
        # check if event is assigned, otherwise state pin invalid
        pl = pls[0]
        if pl.event_id is None:
            abort(make_response('PIN invalid.', 401))
        return make_response('PIN valid.', 200)
