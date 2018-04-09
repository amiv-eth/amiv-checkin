
# global imports

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField


class CreateNewFreebieEvent(FlaskForm):
    """
    Create a new Freebie Event
    """
    title = StringField('Event Title', default="Bier & Wurst")
    description = TextAreaField('Description (Date, Time, Location, ...)')
    max_freebies = IntegerField('Maximum number of Freebies allowed for one member (natural number >= 1)')
    submit = SubmitField('Start new Freebie Event')
