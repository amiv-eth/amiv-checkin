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

    def set_event(self, event_id):
        """ Set the event_id for this instance of the class """
        self.event_id = event_id

    def _get_userid_from_legi(self, legi):
        """ Fetch the user_id from a legi number """
        _filter = '/users?where={"legi":"%s"}' % legi
        r = requests.get(self.api_url + _filter,
                         auth=self.auth_obj)
        if r.status_code is 200:
            return r.json()['_id']
        return "Error: No user found"

    def _get_userid_from_nethz(self, nethz):
        """ Fetch the user_id from a nethz username """
        _filter = '/users?where={"nethz":"%s"}' % nethz
        r = requests.get(self.api_url + _filter,
                         auth=self.auth_obj)
        if r.status_code is 200:
            return r.json()['_id']
        return "Error: No user found"

    def _get_userid_from_email(self, email):
        """ Fetch the user_id from a mail adress """
        _filter = '/users?where={"email":"%s"}' % email
        r = requests.get(self.api_url + _filter,
                         auth=self.auth_obj)
        if r.status_code is 200:
            if len(r.json().keys()) is 1:
                return r.json()['_id']
        return "Error: Multiple entries found or no user found"

    def get_userid_from_info(self, info):
        """ Choose the function to use to fetch the u_id """
        if '@' in info:
            user_id = self._get_userid_from_email(info)
        elif info.isalpha():
            user_id = self._get_userid_from_nethz(info)
        else:
            if info[0] is 'S':
                info.replace('S', '')
            user_id = self._get_userid_from_legi(info)
        return user_id

    def checkin_field(self, info):
        """ Check in a user to an event by flipping the checked_in value """
        user_id = self._get_userid_from_info(info)
        if 'Error' in user_id:
            return False
        _filter = '?where={"user":"%s", "event":"%s"}' % user_id, self.event_id
        r = requests.get(self.api_url + '/eventsignups' + _filter,
                         auth=self.auth_obj)
        if r.status_code != 200:
            return False
        etag = r.json()['_etag']
        url = self.api_url + '/eventsignups/' + self.event_id
        header = {'If-Match': etag}
        payload = {"checked_in": "True"}
        _filter = '?where={"user":"%s"}' % user_id
        r = requests.patch(url + _filter,
                           auth=self.auth_obj,
                           headers=header,
                           data=payload)
        return r.status_code == 200

    def checkout_field(self, info):
        """ Check in a user to an event by flipping the checked_in value """
        user_id = self._get_userid_from_info(info)
        _filter = '?where={"user":"%s", "event":"%s"}' % user_id, self.event_id
        r = requests.get(self.api_url + '/eventsignups' + _filter,
                         auth=self.auth_obj)
        if r.status_code != 200:
            return False
        etag = r.json()['_etag']
        url = self.api_url + '/eventsignups/' + self.event_id
        header = {'If-Match': etag}
        payload = {"checked_in": "False"}
        _filter = '?where={"user":"%s"}' % user_id
        r = requests.patch(url + _filter,
                           auth=self.auth_obj,
                           headers=header,
                           data=payload)
        return r.status_code == 200
