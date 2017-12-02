from datetime import datetime, timedelta
import requests


class AMIV_API_Interface:
    """ Interface class to fetch and update data through the AMIV API """
    def __init__(self):
        self.api_url = "https://amiv-api.ethz.ch"
        self.datetime_format = "%Y-%m-%dT%H:%M:%SZ"

        self.token = ""
        self.auth_obj = ""

    def login(self, username, password):
        """ Log in the user to obtain usable token for requests """
        payload = {"user": str(username), "password": password}
        r = requests.post(self.api_url + '/events', data=payload)
        if r.status_code is 201:
            self.token = r.json()['token']
            self.auth_obj = requests.auth.HTTPBasicAuth(self.token, "")

    def get_next_events(self):
        """ Fetch the upcoming events between today and tomorrow """
        low_bound = datetime.today().strftime(self.datetime_format)
        up_bound = datetime.today() + timedelta(days=1)
        up_bound = up_bound.strftime(self.datetime_format)
        _range = '{"time_start":{"$gt":"'+low_bound+'","$lt":"'+up_bound+'"}}'
        r = requests.get(self.api_url + '/events?where=' + _range)
        return r.json()

    def get_signups_for_event(self, event_id):
        """ Fetch the list of participants for a specific event """
        _filter = '/eventsignups?where={"event":"%s"}' % event_id
        r = requests.get(self.api_url + _filter, auth=self.auth_obj)
        return r.json()

    def checkin_field(self, user_id, event_id):
        """ Check in a user to an event by flipping the checked_in valuei """
        r = requests.get(self.api_url + '/eventsignups/' + event_id,
                         auth=self.auth_obj)
        if r.status_code != 200:
            return False
        etag = r.json()['_etag']
        url = self.api_url + '/eventsignups/' + event_id
        header = {'If-Match': etag}
        payload = {"checked_in": "True"}
        _filter = '?where={"user":"%s"}' % user_id
        r = requests.patch(url + _filter,
                           auth=self.auth_obj,
                           headers=header,
                           data=payload)
        return r.status_code == 200
