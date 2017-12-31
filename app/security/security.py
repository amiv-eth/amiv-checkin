# global imports
from flask import current_app as app
from flask import request, abort, make_response
from ipaddress import ip_address, ip_network
import datetime

# local imports
from .models import IPBan
from .. import db


def check_banned_ip():
    """
    Checks each request origin IP and aborts if IP is banned.
    """
    n_ipban = IPBan.query.filter(IPBan.ip == str(request.remote_addr))\
                         .filter(IPBan.banned == True)\
                         .count()

    if n_ipban > 0:
        abort(make_response('Too many failed login tries.', 429))


def init(capp):
    """ use this function to register the before_request check """
    capp.before_request(check_banned_ip)


def register_failed_login_attempt():
    """
    call this function on a failed login attempt
    """
    # get config details
    max_tries = app.config.get('SECURITY_MAX_FAILED_LOGIN_TRIES')
    if max_tries is None:
        raise Exception('SECURITY_MAX_FAILED_LOGIN_TRIES config is not set. Must be int.')
    allowed_subnets = app.config.get('SECURITY_UNBANNABLE_SUBNETS')
    if allowed_subnets is None:
        raise Exception('SECURITY_UNBANNABLE_SUBNETS config is not set. Must be list of strings.')

    # either get existing IPBan or create new
    ipban = IPBan.query.filter(IPBan.ip == str(request.remote_addr)).one_or_none()
    if ipban is None:
        ipban = IPBan(ip=request.remote_addr, failed_tries=0)
        db.session.add(ipban)

    # increase failed_tries counter
    ipban.failed_tries = ipban.failed_tries + 1

    # find if ip is in unbannable subnets
    bannable = True
    for subnet in [ip_network(subnetstr) for subnetstr in allowed_subnets]:
        if ip_address(request.remote_addr) in subnet:
            bannable = False
            break

    # ban if max tries is reached and ip not in un-bannable networks
    if bannable and (ipban.failed_tries >= max_tries):
        ipban.banned = True
        ipban.time_ban_start = datetime.datetime.now()

    # commit to DB
    db.session.commit()


def register_login_success():
    """
    call this function on a successful login attempt
    """
    # either get existing IPBan or create new
    ipban = IPBan.query.filter(IPBan.ip == str(request.remote_addr)).one_or_none()
    if ipban is not None:
        ipban.failed_tries = 0
        db.session.commit()
