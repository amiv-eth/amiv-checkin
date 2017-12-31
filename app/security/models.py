
from app import db


class IPBan(db.Model):
    """
    A single IP to be banned.
    """

    __tablename__ = 'ipbanns'

    _id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(32), nullable=False)
    failed_tries = db.Column(db.Integer, nullable=False, default=0)
    time_ban_start = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    banned = db.Column(db.Boolean, nullable=False, default=False)
