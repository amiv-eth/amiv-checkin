
# global imports
from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField


def create_default_gv_title():
    dtn = datetime.now()
    yy = str(dtn.year)[-2:]
    if dtn.month <= 6:
        sem = 'FS'
    else:
        sem = 'HS'
    return 'AMIV GV ' + sem + yy


class CreateNewGVForm(FlaskForm):
    """
    Create a new GV with Title, description, and start_time
    """
    title = StringField('GV Title', default=create_default_gv_title())
    description = TextAreaField('GV Description (Date, Time, Location, Agenda, ...)', )
    submit = SubmitField('Start new GV')
