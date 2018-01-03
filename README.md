amiv-checkin
============

A tool to track attendance for AMIV events written in Python 3. It allows to see a list of all signed up people of an event, GV, or a PVK
course (PVK attendance tracking not yet implemented.) Every participant can then be checked-in and out either via the
web frontend or JSON based API endpoints. In conjuction with the [check-in Android App](https://gitlab.ethz.ch/amiv/amiv-checkin-app)
amiv-checkin offers quick and efficient tracking of attendance statistics and admission. 

The tool currently supports two types of events:
- AMIV Events from the amivapi
- General Assemblies (GV) taking it's member data from amivapi

As helpers (like Kulturis) might not have the full administrative rights to modify participant lists in the data
backends (eventsignups in amivapi), this tool allows the delegation of permission via an 8 digit PIN. The PIN can be
used to authenticate check-in or check-out participants of a single event by anyone who knows the PIN.
To setup the attendancd tracking for an event, a user with sufficient privileges has to initialize the PIN.

Many thanks to the great FLASK tutorials [here](https://scotch.io/tutorials/build-a-crud-web-app-with-python-and-flask-part-one) and [here](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world).
  

## Deployment

< add infos for deployment here once figured out how to do it >


## Development

To start the app locally for development, do the following (shell code is for the [fish-shell](https://fishshell.com/)):

1. clone this repo
1. create a python3 virtual environment: `virtualenv env`
1. and activate it: `source env/bin/activate.fish`
1. install the requirements inside the virtualenv: `pip install -r requirements.txt`
1. set the following environment variables: `set -x FLASK_APP run.py`, `set -x FLASK_CONFIG development`, and `set -x FLASK_DEBUG 1`
1. create the local settings file with all the juicy secrets inside in `instance/config.py`. The two follwing options must be set: `SQLALCHEMY_DATABASE_URI` and `SECRET_KEY`.
1. run the flask app: `flask run`


## API Endpoints Documentation

This is not very important if you do not want to build your own software interfacing with this webapp.

There are three endpoints available:


### HTTP POST to /checkpin

Checks if a pin is valid for authentication or not.

Needs one `application/x-www-form-urlencoded` data field:
- `pin` : 6 or 8 digit pin to check

Responses:
- `HTTP 400` : on malformed request
- `HTTP 401` : on invalid pin (or pin is valid but no tracking setup yet)
- `HTTP 200` : on valid pin

There is a human readable status string message in the response body.


### HTTP POST to /mutate

Check user in or out of event.

Needs three `application/x-www-form-urlencoded` data fields:
- `pin` : 6 or 8 digit pin
- `checkmode` : choose action: 'in' for check-in or 'out' for check-out
- `info` : unique identifier of the participant (nethz, e-mail, or legi number) 

Responses:
- `HTTP 400` : on malformed request or if the action failed
- `HTTP 401` : on invalid pin (or pin is valid but no tracking setup yet)
- `HTTP 200` : on success

There is a human readable status string message in the response body with an error description for failed actions.

### HTTP GET to /checkin_update_data

Retreive participant list and statistics in JSON format.

Needs one request header field:
- `pin` : 6 or 8 digit pin (authentication to this endpoint can also be done via cookie set from the web frontend)

Responses:
- `HTTP 400` : on malformed request
- `HTTP 401` : on invalid pin or login failure
- `HTTP 200` : on success

In the response body, there is `application/json` content with two sections: `signups` and `statistics`. Example response:
```json
{
  "signups": [
    {
      "_id": "5a2285d4977d36000aba4f15", 
      "checked_in": true, 
      "email": "pablo573798586@example.com", 
      "firstname": "Pablo573798584", 
      "lastname": "AMIV573798585", 
      "legi": null, 
      "membership": "extraordinary", 
      "nethz": "user573798583"
    }, 
    {
      "_id": "5a2285d4977d36000aba4ee9", 
      "checked_in": false, 
      "email": "pablo573798402@example.com", 
      "firstname": "Pablo573798400", 
      "lastname": "AMIV573798401", 
      "legi": null, 
      "membership": "honorary", 
      "nethz": "user573798399"
    }, 
    <<< many more >>>
  ], 
  "statistics": [
    {
      "key": "Total Signups", 
      "value": 15
    }, 
    {
      "key": "Current Attendance", 
      "value": 2
    }
  ]
}
``` 
