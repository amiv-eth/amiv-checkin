from app import db


class EventCount(db.Model):
    """
    Table that stores the counts for events of the count type
    """
    __tablename__ = 'event_count'

    user_id = db.Column(db.String(128), nullable=False, primary_key=True)

    __table_args__ = (db.UniqueConstraint('user_id', 'event_id'), )

    # relation to event
    event_id = db.Column(db.String(128),
                         db.ForeignKey('presencelists.event_id'),
                         nullable=False,
                         primary_key=True)

    count = db.Column(db.Integer, nullable=False)
