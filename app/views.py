# views.py

from flask import render_template

from app import app

@app.route('/')
def index():

	if current_user.is_authenticated:
		return redirect(url_for('checkin.checkin'))

    return redirect(url_for('login.login'))
    