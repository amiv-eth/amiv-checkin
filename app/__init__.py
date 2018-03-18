# app/__init__.py

# third-party imports
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from werkzeug.contrib.fixers import ProxyFix

# local imports
from config import app_config

import pymysql
pymysql.install_as_MySQLdb()

# db variable initialization
db = SQLAlchemy()

# get flask login manager
login_manager = LoginManager()


def create_app(config_name, file_based_secrets=True):
    # initialize flask app and configure
    app = Flask(__name__, instance_relative_config=file_based_secrets)
    app.config.from_object(app_config[config_name])
    if file_based_secrets:
        app.config.from_pyfile('config.py')

    # apply proxy-fix to get correct remote-ip
    num_proxies = app.config.get('SECURITY_NUM_PROXY_LEVELS')
    if num_proxies is None:
        raise Exception('SECURITY_NUM_PROXY_LEVELS config is not set. Must be int.')
    if num_proxies > 0:
        app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=num_proxies)

    # initialize ORM
    db.init_app(app)

    # add login functionality from flask-login
    login_manager.init_app(app)
    login_manager.login_message = "You must be logged in to access this page."
    login_manager.login_view = "login.login"

    # add database migration from flask-migrate
    Migrate(app, db)

    # add flask-bootstrap
    Bootstrap(app)

    # add all persistent data models
    from app import models
    from .connectors import gvtool_models
    from .security import models

    # add security module
    from .security import security
    security.init(app)

    # add all blueprints
    from .login import login_bp
    app.register_blueprint(login_bp)

    from .checkin import checkin_bp
    app.register_blueprint(checkin_bp)

    from .mutate import mutate_bp
    app.register_blueprint(mutate_bp)

    from .gvtool import gvtool_bp
    app.register_blueprint(gvtool_bp)

    from .event import event_bp
    app.register_blueprint(event_bp)

    # app initalized
    return app
