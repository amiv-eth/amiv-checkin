
from app import db


class GVEvent(db.Model):
    """
    Event list is not supplied by external API but locally hosted.
    This is used here for GVs.
    """

    __tablename__ = 'gvtool_events'

    _id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(10000))
    time_start = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # relation to signup
    signups = db.relationship('GVSignup', order_by='GVSignup._id', back_populates='GVEvent')

    # # implement the signup_count and spots key
    # def __getitem__(self, key):
    #     if key == 'signup_count':
    #         return len(self.signups)
    #     elif key == 'spots':
    #         return 0
    #     else:
    #         return super().__getitem__(key)


class GVSignup(db.Model):
    """
    A signup to a GV plus the checked-in state.
    """
    __tablename__ = 'gvtool_signups'

    _id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), nullable=False)
    checked_in = db.Column(db.Boolean)

    __table_args__ = (db.UniqueConstraint('user_id', 'gvevent_id'), )

    # relation to event
    gvevent_id = db.Column(db.Integer, db.ForeignKey('gvtool_events._id'))
    GVEvent = db.relationship('GVEvent', back_populates='signups')

    # relation to log
    logs = db.relationship('GVLog', order_by='GVLog.timestamp', back_populates='GVSignup')

    # def __init__(self):
    #     super().__init__()
    #     self.user = None
    #
    # def assign_user(self, user):
    #     self.user = user
    #
    # def __getitem__(self, key):
    #     if key == 'user':
    #         return self.user
    #     else:
    #         return super().__getitem__(key)


class GVLog(db.Model):
    """
    One log-book entry on when a user checked in or out of an event.
    """

    __tablename__ = 'gvtool_logs'

    _id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    checked_in = db.Column(db.Boolean)  # new state of checked_in field

    # relation to gvsignup
    gvsignup_id = db.Column(db.Integer, db.ForeignKey('gvtool_signups._id'))
    GVSignup = db.relationship('GVSignup', back_populates='logs')
