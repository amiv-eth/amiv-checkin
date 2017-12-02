# app/checkin/views.py

from flask import flash, redirect, render_template, url_for
from flask_login import login_required, login_user, logout_user

from . import checkin_bp
from .forms import CheckForm

@checkin_bp.route('/checkin')
#@login_required
def checkin():
    """
    Handle requests to the /register route
    Add an employee to the database through the registration form
    """

    checkform = CheckForm()

    # load registration template
    return render_template('checkin/checkin.html', form=checkform, title='AMIV Check-In')

    