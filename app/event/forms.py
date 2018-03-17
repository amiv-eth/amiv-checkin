from flask_wtf import FlaskForm
from wtforms import RadioField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional


class EventTypeForm(FlaskForm):

    eventtype = RadioField('Event type',
                           validators=[DataRequired()],
                           choices=[
                               ('in_out', 'Check in/out'),
                               ('counter', 'Counter')])

    # TODO: Add counter validation
    maxcounter = IntegerField(
        'Maximum counter',
        validators=[Optional()],
        render_kw={'autofocus': True, 'onFocus': 'this.select();'})

    submit = SubmitField('Submit')
