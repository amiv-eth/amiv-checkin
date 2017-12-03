
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField
from wtforms.validators import DataRequired

class CheckForm(FlaskForm):
    """
    Form for users to create new account
    """
    checkmode = RadioField('checkmode', validators=[DataRequired()], choices=[('in', 'Check-In'),('out','Check-Out')])
    datainput = StringField('Legi #, nethz, or email', validators=[DataRequired()])
    submit = SubmitField('Submit')
