from datetime import datetime, timedelta
import requests


class AMIV_API_Interface:
    """ Interface class to fetch and update data through the AMIV API """
    def __init__(self):
        self.api_url = "https://amiv-api.ethz.ch"
        self.datetime_format = "%Y-%m-%dT%H:%M:%SZ"

        self.human_string = "AMIV Events"
        self.human_string = "amivapi_connector"

        self.token = ""
        self.auth_obj = ""

        self.human_string = "AMIV Events"
        self.id_string = "conn_amivapi"

    def login(self, username, password):
        """ Log in the user to obtain usable token for requests """
        payload = {"user": str(username), "password": password}
        r = requests.post(self.api_url + '/sessions', data=payload)
        if r.status_code is 201:
            self.token = r.json()['token']
            self.auth_obj = requests.auth.HTTPBasicAuth(self.token, "")
            return self.token
        else:
            raise Exception('Invalid username or password')

    def token_login(self, token):
        """ Log in the user by storing their session token in this class """
        self.token = token
        self.auth_obj = requests.auth.HTTPBasicAuth(self.token, "")

    def get_next_events(self):
        """ Fetch the upcoming events between today and tomorrow """
        low_bound = datetime.today().strftime(self.datetime_format)
        up_bound = datetime.today() + timedelta(days=100)
        up_bound = up_bound.strftime(self.datetime_format)
        _range = '{"time_start":{"$gt":"'+low_bound+'","$lt":"'+up_bound+'"}}'
        r = requests.get(self.api_url + '/events?where=' + _range)
        if min(r.json()['total'], r.json()['max_results']) is 0:
            raise Exception("No Events found in the next 100 days")
        response = list()
        for key, event in r.json().iteritems():
            response.append({
                             '_id': event['_id'],
                             'title': event['title'],
                             'spots': event['spots'],
                             'signup_count': event['signup_count'],
                             'time_start': event['time_start']})
        return response

    def get_signups_for_event(self, event_id):
        """ Fetch the list of participants for a specific event """
        _filter = ('/eventsignups?where={"event":"%s"}&embedded={"user":1}'
                   % event_id)
        r = requests.get(self.api_url + _filter, auth=self.auth_obj)
        if min(r.json()['total'], r.json()['max_results']) is 0:
            raise Exception("No eventsignups found for this event")
        response = list()
        for key, eventsignup in r.json().iteritems():
            user_info = eventsignup['user']
            response.append({
                             'firstname': user_info['firstname'],
                             'lastname': user_info['lastname'],
                             'nethz': user_info['nethz'],
                             'email': user_info['email'],
                             'checked_in': eventsignup['checked_in'],
                             'legi': user_info['legi'],
                             '_id': user_info['_id']})
        return r.json()

    def set_event(self, event_id):
        """ Set the event_id for this instance of the class """
        self.event_id = event_id

    def _get_userinfo_from_userid(self, u_id):
        """ Fetch the userinfos from the user_id """
        r = requests.get(self.api_url + '/users/' + u_id)
        return r.json()

    def _get_userinfo_from_legi(self, legi):
        """ Fetch the user_id from a legi number """
        _filter = '/users?where={"legi":"%s"}' % legi
        r = requests.get(self.api_url + _filter,
                         auth=self.auth_obj)
        if r.status_code is 200:
            return r.json()
        raise Exception("Error: No user found")

    def _get_userinfo_from_nethz(self, nethz):
        """ Fetch the user_id from a nethz username """
        _filter = '/users?where={"nethz":"%s"}' % nethz
        r = requests.get(self.api_url + _filter,
                         auth=self.auth_obj)
        if r.status_code is 200:
            return r.json()
        raise Exception("Error: No user found")

    def _get_userinfo_from_email(self, email):
        """ Fetch the user_id from a mail adress """
        _filter = '/users?where={"email":"%s"}' % email
        r = requests.get(self.api_url + _filter,
                         auth=self.auth_obj)
        if r.status_code is 200:
            if len(r.json().keys()) is 1:
                return r.json()
        raise Exception("Error: Multiple entries found or no user found")

    def _get_userinfo_from_info(self, info):
        """ Choose the function to use to fetch the u_id """
        if '@' in info:
            user_info = self._get_userinfo_from_email(info)
        elif info.isalpha():
            user_info = self._get_userinfo_from_nethz(info)
        else:
            if info[0] is 'S':
                info.replace('S', '')
            user_info = self._get_userinfo_from_legi(info)
        return user_info

    def checkin_field(self, info):
        """ Check in a user to an event by flipping the checked_in value """
        user_id = self._get_userid_from_info(info)['_id']
        _filter = '?where={"user":"%s", "event":"%s"}' % user_id, self.event_id
        r = requests.get(self.api_url + '/eventsignups' + _filter,
                         auth=self.auth_obj)
        if r.status_code != 200:
            raise Exception("Error: Could not find eventsignup entry")
        if r.json()['checked_in'] is True:
            raise Exception("Error: User already checked in")
        etag = r.json()['_etag']
        url = self.api_url + '/eventsignups'
        header = {'If-Match': etag}
        payload = {"checked_in": "True"}
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
            raise Exception("Error: Could not find the eventsignup entry")
        if r.json()['checked_in'] is False:
            raise Exception("Error: User already checked out or absent")
        etag = r.json()['_etag']
        url = self.api_url + '/eventsignups'
        header = {'If-Match': etag}
        payload = {"checked_in": "False"}
        r = requests.patch(url + _filter,
                           auth=self.auth_obj,
                           headers=header,
                           data=payload)
        return r.status_code == 200
