
from app import db


class FreebieEvent(db.Model):
    """
    Event list is not supplied by external API but locally hosted.
    This is used here for Freebies.
    """

    __tablename__ = 'freebies_events'

    _id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(10000))
    time_start = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    max_freebies = db.Column(db.Integer)

    # relation to signup
    signups = db.relationship('FreebieSignup', order_by='FreebieSignup._id', back_populates='FreebieEvent')


class FreebieSignup(db.Model):
    """
    A signup to a Freebie plus the checked-in state.
    """
    __tablename__ = 'freebies_signups'

    _id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), nullable=False)
    freebies_taken = db.Column(db.Integer)

    __table_args__ = (db.UniqueConstraint('user_id', 'freebieevent_id'), )

    # relation to event
    freebieevent_id = db.Column(db.Integer, db.ForeignKey('freebies_events._id'))
    FreebieEvent = db.relationship('FreebieEvent', back_populates='signups')

    # relation to log
    logs = db.relationship('FreebieLog', order_by='FreebieLog.timestamp', back_populates='FreebieSignup')

    def set_user(self, user):
        self.user = user

    def get_user(self):
        return self.user


class FreebieLog(db.Model):
    """
    One log-book entry for the freebie log
    """

    __tablename__ = 'freebies_logs'

    _id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    freebies_taken = db.Column(db.Integer)  # new state of freebies_taken field

    # relation to gvsignup
    freebiesignup_id = db.Column(db.Integer, db.ForeignKey('freebies_signups._id'))
    FreebieSignup = db.relationship('FreebieSignup', back_populates='logs')
