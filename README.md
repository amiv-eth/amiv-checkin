# AMIV Check-in

A tool to track attendance for AMIV events written in Python 3. It allows to see a list of all signed up people of an event, GV, or a PVK
course (PVK attendance tracking not yet implemented.) Every participant can then be checked-in and out either via the
web frontend or JSON based API endpoints. In conjunction with the [check-in Android App](https://gitlab.ethz.ch/amiv/amiv-checkin-app) and [iOS App](https://gitlab.ethz.ch/amiv/amiv-checkin-app-ios)
amiv-checkin offers quick and efficient tracking of attendance statistics and admission.

The tool currently supports two types of events:
- AMIV Events from the amivapi
- General Assemblies (GV) taking it's member data from amivapi

As helpers (like Kulturis) might not have the full administrative rights to modify participant lists in the data
backends (eventsignups in amivapi), this tool allows the delegation of permission via an 8 digit PIN. The PIN can be
used to authenticate check-in or check-out participants of a single event by anyone who knows the PIN.
To setup the attendance tracking for an event, a user with sufficient privileges has to initialize the PIN.

Many thanks to the great FLASK tutorials [here](https://scotch.io/tutorials/build-a-crud-web-app-with-python-and-flask-part-one) and [here](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world).

If you want to write your own frontend for checkin / checkout, see the API documentation at [README_API.md](README_API.md).

## Deployment

is done via GitLab CI pipeline. Launch the "deploy" job manually from the commits view in GitLab to deploy the app to the ISG.EE server.
The webapp is reachable at [checkin.amiv.ethz.ch](https://checkin.amiv.ethz.ch).
uWSGI is used to serve the app behind the ISGs apache web server and the [ISG's SQL server](https://mysql.ee.ethz.ch) holds the database.

## Development

To start the app locally for development, do the following (shell code is for the [fish-shell](https://fishshell.com/)):

1. clone this repo
1. create a python3 virtual environment: `virtualenv env`
1. and activate it: `source env/bin/activate.fish`
1. install the requirements inside the virtualenv: `pip install -r requirements.txt`
1. set the following environment variables: `set -x FLASK_APP run.py`, `set -x FLASK_CONFIG development`, and `set -x FLASK_DEBUG 1`
1. create the local settings file with all the juicy secrets inside in `instance/config.py`. The two following options must be set: `SQLALCHEMY_DATABASE_URI` and `SECRET_KEY`. See next section.
1. run the flask app: `flask run`

### Creating a local DB for development

1. Install Mysql (on MacOs: `brew install mysql`) and make sure it's running (on MacOS: `brew services start mysql`)
2. Install a MySql client for python, for instance `mysqlclient` (`pip install mysqlclient`)
3. Crete user and database on mysql:
   1. Connect to MySQL: `mysql -u root`
   2. Create user `CREATE USER '%USER%'@'localhost' IDENTIFIED BY '%PASSWORD%';`, replacing %USER% and %PASSWORD%
   3. Create DB: `CREATE DATABASE %DB_NAME%;`, replacing %DB_NAME%
   4. Give all privileges `GRANT ALL PRIVILEGES ON %DB_NAME%.* TO '%USER%'@'localhost';`, replacing %DB_NAME% and %USER%
4. Edit your `config.py`:
   1. Set `SECRET_KEY` to some random string
   2. Set `SQLALCHEMY_DATABASE_URI` to `mysql://%USER%:%PASSWORD%@localhost/%DB_NAME%`
5. Upgrade DB to correct state: `flask db upgrade`

### How to handle database changes

Do the following if your code changes require any changes of the database schema:

1. Make sure that your local database schema is equal to the last committed migration file (found in the directory `migrations/`)
2. Generate new migration file with `flask db migrate`.
3. Apply your changes to the local development database with `flask db upgrade`.
4. Verify that everything is ok with the database schema.
5. Commit the created migrations file. DO NOT CHANGE any migration file which is already committed!

### Set up on Windows

1. Get the latest version of python version 3.x at: https://www.python.org/downloads/
2. For setting up flask see the installation guide at the docs: http://flask.pocoo.org/docs/0.12/installation/
      ```bash
      cd c:/users/path/to/project/root
      venv\Scripts\activate
      pip install flask
      pip install requirements.txt
      ```
      Then to run the flask app quickly for a new cmd paste the code below
      ```bash
      cd c:/users/path/to/project/root
      venv\Scripts\activate
      set FLASK_APP=run_local.py
      set FLASH_CONFIG=development
      set FLASK_DEBUG=1
      flask run
      ```
      Only call flask run once you have finished all the steps
3. Get the latest mySQL _installer_ here: https://dev.mysql.com/downloads/windows/installer/
4. Choose the server only option.
5. After installation the installer will continue to configure the mySQL server, set a password and create a user with password (all still part of the installer)
6. Follow the instructions above for creating a local DB from the step to create a database, but use the separate MySql Command Line Client which is now installed, not cmd. 
   If there are errors check syntax and try with/out quotes/spaces.