# app/__init__.py

# third-party imports
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap

# local imports
from config import app_config

# db variable initialization
db = SQLAlchemy()

# get flask login manager
login_manager = LoginManager()

def create_app(config_name):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_message = "You must be logged in to access this page."
    login_manager.login_view = "login.login"

    migrate = Migrate(app, db)

    Bootstrap(app)


    from app import models


    from .login import login_bp
    app.register_blueprint(login_bp)

    from .checkin import checkin_bp
    app.register_blueprint(checkin_bp)

    from .mutate import mutate_bp
    app.register_blueprint(mutate_bp)

    return app
