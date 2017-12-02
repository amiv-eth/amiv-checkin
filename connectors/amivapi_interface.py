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


if __name__ is "__main__":
    i = AMIV_API_Interface()
    print(i.get_next_events())
    print(i.get_signups_for_event('1'))
