# API Endpoints Documentation

This is not very important if you do not want to build your own software interfacing with this webapp.

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
    ... and many more ... 
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
