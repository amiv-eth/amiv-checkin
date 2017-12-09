from datetime import datetime, timedelta
import requests
from math import ceil


class AMIV_API_Interface:
    """ Interface class to fetch and update data through the AMIV API """
    def __init__(self):
        self.api_url = "https://amiv-api.ethz.ch"
        self.datetime_format = "%Y-%m-%dT%H:%M:%SZ"

        self.token = ""
        self.auth_obj = ""
        self.event_id = ""

        self.human_string = "AMIV Events"
        self.id_string = "conn_amivapi"

    def login(self, username, password):
        """ Log in the user to obtain usable token for requests """
        payload = {"username": str(username), "password": str(password)}
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

    def _api_get(self, url):
        r = requests.get(self.api_url + url, auth=self.auth_obj)
        if r.status_code != 200:
            raise Exception('GET failed - URL:{} - HTTP {}'.format(r.url, r.status_code))
        return r

    def get_next_events(self):
        """ Fetch the upcoming events between today and tomorrow """
        # low_bound = datetime.today() - timedelta(days=2)
        # low_bound = low_bound.strftime(self.datetime_format)
        # up_bound = datetime.today() + timedelta(days=100)
        # up_bound = up_bound.strftime(self.datetime_format)
        # _range = '{"time_start":{"$gt":"'+low_bound+'","$lt":"'+up_bound+'"}}'
        # r = self._api_get('/events?where=' + _range)
        r = self._api_get('/events')
        _events = [x for x in r.json()['_items']]

        # get all events from the rest of the pages
        ntotal = r.json()['_meta']['total']
        npage = r.json()['_meta']['max_results']
        if min(ntotal, npage) is 0:
            raise Exception("No Events found in the next 100 days.")

        for p in range(2, int(ceil(ntotal/npage))+1):
            #r = self._api_get('/events?page={}&where={}'.format(str(p), _range))
            r = self._api_get('/events?page={}'.format(str(p)))
            _events.extend(r.json()['_items'])

        response = list()
        for event in _events:

            # assemble info for event
            ev = dict()
            ev['_id'] = event['_id']
            if 'title_en' in event and event['title_en']:
                ev['title'] = event['title_en']
            else:
                ev['title'] = event['title_de']
            if 'spots' in event:
                ev['spots'] = event['spots']
            else:
                ev['spots'] = "unlimited"
            if 'signup_count' in event:
                ev['signup_count'] = event['signup_count']
            if 'time_start' in event:
                ev['time_start'] = datetime.strptime(event['time_start'], self.datetime_format)
            response.append(ev)

        return response

    def set_event(self, event_id):
        """ Set the event_id for this instance of the class """
        self.event_id = event_id

    def get_signups_for_event(self):
        """ Fetch the list of participants for a specific event """
        r = self._api_get('/eventsignups?where={"event":"%s"}&embedded={"user":1}' % self.event_id)
        _signups = [x for x in r.json()['_items']]

        # get all signups from all pages
        ntotal = r.json()['_meta']['total']
        npage = r.json()['_meta']['max_results']

        for p in range(2, int(ceil(ntotal / npage))+1):
            r = self._api_get('/eventsignups?where={"event":"%s"}&embedded={"user":1}&page=%s' % (self.event_id, str(p)))
            _signups.extend(r.json()['_items'])

        response = list()
        for eventsignup in _signups:
            user_info = eventsignup['user']
            # translate non-existing value to None
            if 'checked_in' in eventsignup:
                cki = eventsignup['checked_in']
            else:
                cki = None
            # assemble signup dict
            response.append({
                             'firstname': user_info['firstname'],
                             'lastname': user_info['lastname'],
                             'nethz': user_info['nethz'],
                             'email': user_info['email'],
                             'checked_in': cki,
                             'legi': user_info['legi'],
                             '_id': user_info['_id']})

        return response

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
