# API Endpoints Documentation

_This is not very important if you do not want to build your own software interfacing with this webapp._

To test the responses quickly, use Postman (getpostman.com) and create a GET/POST request to the url of a running checkin server with the extension (eg http://checkin.amiv.ethz.ch/checkpin), ensure to set pin etc in th header.

There are three endpoints available:


## POST /checkpin

Checks if a pin is valid for authentication or not.

Needs one `application/x-www-form-urlencoded` data field:
- `pin` : 6 or 8 digit pin to check

Responses:
- `HTTP 400` : on malformed request
- `HTTP 401` : on invalid pin (or pin is valid but no tracking setup yet)
- `HTTP 200` : on valid pin

There is a human readable status string message in the response body.


## POST /mutate

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

## GET /checkin_update_data

Retreive participant list and statistics in JSON format.

Needs one request header field:
- `pin` : 6 or 8 digit pin (authentication to this endpoint can also be done via cookie set from the web frontend)

Responses:
- `HTTP 400` : on malformed request
- `HTTP 401` : on invalid pin or login failure
- `HTTP 200` : on success

In the response body, there is `application/json` content with two sections: `signups` and `statistics`. Example response (for a GV in this case):
```json
{
    "eventinfos": {
        "_id": "1",
        "description": "asasfdfs",
        "event_type": "AMIV General Assemblies",
        "signup_count": 1,
        "spots": 0,
        "time_start": "Sat, 17 Mar 2018 10:31:52 GMT",
        "title": "Test GV - Coding WE"
    },
    "signups": [
        {
            "checked_in": true,
            "email": "pablo@amivemail.ch",
            "firstname": "pablo",
            "lastname": "PVK",
            "legi": "12121212",
            "membership": "regular",
            "nethz": "pablo",
            "signup_id": 1,
            "user_id": "59eb616cedcb11000ae5ecde"
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
        ... and many more ... 
    ],
    "statistics": [
        {
            "key": "Regular Members",
            "value": 1
        },
        {
            "key": "Extraordinary Members",
            "value": 0
        },
        {
            "key": "Honorary Members",
            "value": 0
        }
        ... etc ...
    ]
}
``` 
