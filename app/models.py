# app/models.py

from flask_login import UserMixin

from app import db, login_manager


class PresenceList(UserMixin, db.Model):
    """
    Create a Presence List table
    """

    # Ensures table will be named in plural and not in singular
    # as is the name of the model
    __tablename__ = 'presencelists'

    id = db.Column(db.Integer, primary_key=True)
    conn_type = db.Column(db.String(128))
    pin = db.Column(db.Integer, index=True, unique=True)
    token = db.Column(db.String(128))
    event_id = db.Column(db.String(128))


# Set up user_loader
@login_manager.user_loader
def load_user(user_id):
    return PresenceList.query.get(int(user_id))
