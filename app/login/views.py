# app/login/views.py

from flask import flash, redirect, render_template, url_for, request
from flask_login import login_required, login_user, logout_user

from . import login_bp
from .forms import PinLoginForm, CredentialsLoginForm, ChooseEventForm
from .. import db
from ..models import Employee

@login_bp.route('/')
def home():
    return redirect(url_for('login.login'))


@login_bp.route('/login', methods=['GET','POST'])
def login():
    """
    Handle requests to the /login route
    """

    # create forms
    pinform = PinLoginForm()
    credform = CredentialsLoginForm()

    if request.method == 'POST':
        if 'method_PIN' in request.values:
            if pinform.validate_on_submit():
                if False:
                    # try pin login here
                    flash('PIN validation succeeded.')
                else:
                    flash('Invalid PIN.')
                    return redirect(url_for('checkin.checkin'))
                    
        elif 'method_Cred' in request.values:
            if credform.validate_on_submit():
                if False:
                    # try credentials login here
                    flash('Credentials OK')
                else:
                    flash('Invalid username or password.')
                    return redirect(url_for('login.chooseevent'))
        else:
            print('Did not find correct hidden value in POST request.')
            abort(500)

    # load login template
    return render_template('login/login.html', pinform=pinform, credform=credform, title='Login')


@login_bp.route('/chooseevent', methods=['GET','POST'])
def chooseevent():
    """
    Handle requests to the /chooseevent route
    """

    chooseeventform = ChooseEventForm()

    if request.method == 'POST':
        if chooseeventform.validate_on_submit():
            if False:
                # try credentials login here
                pass
            else:
                flash('Invalid username or password.')
                return redirect(url_for('checkin.checkin'))

    # load login template
    return render_template('login/chooseevent.html', form=chooseeventform, title='Choose Event')
