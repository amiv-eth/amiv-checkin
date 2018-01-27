amiv-checkin
============

A tool to track attendance for AMIV events written in Python 3. It allows to see a list of all signed up people of an event, GV, or a PVK
course (PVK attendance tracking not yet implemented.) Every participant can then be checked-in and out either via the
web frontend or JSON based API endpoints. In conjunction with the [check-in Android App](https://gitlab.ethz.ch/amiv/amiv-checkin-app)
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
1. create the local settings file with all the juicy secrets inside in `instance/config.py`. The two follwing options must be set: `SQLALCHEMY_DATABASE_URI` and `SECRET_KEY`.
1. run the flask app: `flask run`
