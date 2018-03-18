
from flask import redirect, url_for, abort
from flask_login import login_required, logout_user, current_user

from ..models import PresenceList
from .. import db
from . import login_bp


@login_bp.route('/logout_and_delete_pin')
@login_required
def logout_and_delete_pin():
    """
    Handle requests to the /event_logout_and_delete_pin route
    """
    s = PresenceList.query.filter_by(pin=current_user.pin).all()
    if len(s) > 0:
        # only allow pin deletion if no event is assigned yet
        pl = s[0]
        if pl.event_id is not None:
            abort(403)
        # save pin and logout user
        pin_to_remove = current_user.pin
        logout_user()
        # delete wrongly created PresenceList from database
        s = PresenceList.query.filter_by(pin=pin_to_remove).one()
        db.session.delete(s)
        db.session.commit()
    else:
        # should never happen
        logout_user()

    # redirect to the login page
    return redirect(url_for('login.login'))


def beautify_event(raw_event, additional_fields={}):
    """
    Beautify event dict to include strings for display.
    :param raw_event: dict as returned by conn.get_event()
    :param additional_fields: dict which just gets all the keys copied to the output
    :return: dict with signup_string and time_string added
    """
    if 'signup_count' in raw_event:
        if 'spots' not in raw_event or raw_event['spots'] == 0 or raw_event['spots'] is None:
            spots = 'unlimited'
        else:
            spots = raw_event['spots']
        raw_event['signups_string'] = "{} / {}".format(raw_event['signup_count'], spots)
    if 'time_start' in raw_event:
        raw_event['time_string'] = raw_event['time_start'].strftime('%d.%m.%Y %H:%M')
    for k in additional_fields:
        raw_event[k] = additional_fields[k]
    return raw_event
