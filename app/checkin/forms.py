
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField
from wtforms.validators import DataRequired


class CheckForm(FlaskForm):
    """
    Check-in or check-out users.
    """
    checkmode = RadioField('checkmode',
                           validators=[DataRequired()],
                           choices=[('in', 'Check-In'), ('out', 'Check-Out')])
    datainput = StringField('Legi #, nethz, or email',
                            validators=[DataRequired()],
                            render_kw={'autofocus': True, 'onFocus': 'this.select();'})
    submit = SubmitField('Submit')
