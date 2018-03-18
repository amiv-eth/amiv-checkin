from collections import OrderedDict
from datetime import datetime, timedelta
import requests
from math import ceil
from copy import deepcopy
from flask import current_app as app


class AMIV_API_Interface:
    """ Interface class to fetch and update data through the AMIV API """
    def __init__(self):
        self.api_url = app.config.get('AMIV_API_URL')
        if self.api_url is None:
            raise Exception('AMIV_API_URL missing in flask config.')

        self.auth_group_id = app.config.get('AMIV_AUTH_GROUP_ID')
        if self.auth_group_id is None:
            raise Exception('AMIV_AUTH_GROUP_ID missing in flask config')

        self.token = ""
        self.auth_obj = ""
        self.event_id = ""

        self.last_signups = None

        self.human_string = "AMIV Events"
        self.id_string = "conn_amivapi"

        self.datetime_format = "%Y-%m-%dT%H:%M:%SZ"
        self.mem_reg_key = 'regular'
        self.mem_ext_key = 'extraordinary'
        self.mem_hon_key = 'honorary'
        self.non_mem_key = 'none'

    def login(self, username, password):
        """ Log in the user to obtain usable token for requests """
        payload = {"username": str(username), "password": str(password)}
        r = requests.post(self.api_url + '/sessions', data=payload)
        rj = r.json()
        if r.status_code is 201:
            self.token = rj['token']
            self.auth_obj = requests.auth.HTTPBasicAuth(self.token, "")
        else:
            raise Exception('Invalid username or password')

        # check if logged in user is part of authentication group
        uid = rj['user']
        _filter = '{"group":"%s", "user":"%s"}' % (self.auth_group_id, uid)
        r = self._api_get('/groupmemberships?where=' + _filter)
        rj = r.json()
        if len(rj['_items']) != 1:
            raise Exception('User not in Checkin-WebApp authorized group.')

        return self.token

    def token_login(self, token):
        """ Log in the user by storing their session token in this class """
        self.token = token
        self.auth_obj = requests.auth.HTTPBasicAuth(self.token, "")

    def _api_get(self, url):
        r = requests.get(self.api_url + url, auth=self.auth_obj)
        if r.status_code != 200:
            raise Exception('GET failed - URL:{} - HTTP {}'.format(r.url, r.status_code))
        return r

    def _clean_event_obj(self, raw_event):
        """ Re-format the event object from the API to easier, internal representation """
        ev = dict()
        ev['_id'] = str(raw_event['_id'])
        if 'title_en' in raw_event and raw_event['title_en']:
            ev['title'] = raw_event['title_en']
        else:
            ev['title'] = raw_event['title_de']
        if 'spots' not in raw_event or raw_event['spots'] == 0 or raw_event['spots'] is None:
            ev['spots'] = 'unlimited'
        else:
            ev['spots'] = raw_event['spots']
        if 'signup_count' in raw_event:
            ev['signup_count'] = raw_event['signup_count']
        if 'time_start' in raw_event:
            ev['time_start'] = datetime.strptime(raw_event['time_start'], self.datetime_format)
        if 'description_en' in raw_event and raw_event['description_en']:
            ev['description'] = raw_event['description_en']
        else:
            ev['description'] = raw_event['description_de']
        return ev

    def _clean_signup_obj(self, raw_signup):
        user_info = raw_signup['user']
        # translate non-existing value to None (these values are optional in API)
        if 'checked_in' in raw_signup:
            cki = raw_signup['checked_in']
        else:
            cki = None
        if 'legi' in user_info:
            legi = user_info['legi']
        else:
            legi = None
        # assemble signup dict
        return {
            'firstname': user_info['firstname'],
            'lastname': user_info['lastname'],
            'nethz': user_info['nethz'],
            'email': user_info['email'],
            'checked_in': cki,
            'legi': legi,
            'membership': user_info['membership'],
            'user_id': user_info['_id'],
            'signup_id': raw_signup['_id']}

    def get_next_events(self, filter_resp=True):
        """ Fetch the upcoming events between today and tomorrow """
        if (app is not None) and (app.debug is False):
            low_bound = datetime.today() - timedelta(days=2)
            low_bound = low_bound.strftime(self.datetime_format)
            up_bound = datetime.today() + timedelta(days=100)
            up_bound = up_bound.strftime(self.datetime_format)
            _range = '{"time_start":{"$gt":"' + low_bound + '","$lt":"' + up_bound + '"}}'
        else:
            # debug case: do not filter for time, just display all
            # _range = '{"spots":{"$gte":0}}'
            _range = '{}'
        r = self._api_get('/events?where=' + _range)
        _events = [x for x in r.json()['_items']]

        # get all events from the rest of the pages
        ntotal = r.json()['_meta']['total']
        npage = r.json()['_meta']['max_results']
        if min(ntotal, npage) is 0:
            raise Exception("No Events found in the next 100 days.")

        for p in range(2, int(ceil(ntotal/npage))+1):
            r = self._api_get('/events?page={}&where={}'.format(str(p), _range))
            _events.extend(r.json()['_items'])

        if filter_resp:
            return [self._clean_event_obj(e) for e in _events]
        else:
            return _events

    def set_event(self, event_id):
        """ Set the event_id for this instance of the class """
        self.event_id = event_id

    def get_event(self):
        """ Return the event object for the set event_id """
        r = self._api_get('/events/{}'.format(self.event_id))
        return self._clean_event_obj(r.json())

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
            response.append(self._clean_signup_obj(eventsignup))

        # save this for later reference by get_statistics
        self.last_signups = deepcopy(response)

        return response

    def get_statistics(self):
        """ return the statistics string for the last fetched  """
        if self.last_signups is None:
            self.get_signups_for_event()

        stats = OrderedDict()
        stats['Current Attendance'] = 0
        stats['Remaining'] = len(self.last_signups)
        stats['Total Signups'] = len(self.last_signups)
        for u in self.last_signups:
            if u['checked_in'] is True:
                stats['Current Attendance'] = stats['Current Attendance'] + 1
                stats['Remaining'] = stats['Total Signups'] - stats['Current Attendance']
                if stats['Remaining'] < 0:
                    stats['Remaining'] = 0

        return stats

    def _get_userinfo_from_info(self, info):
        """ Choose the function to use to fetch the u_id """
        info = info.strip().lower()  # get rid of whitespace and make everything lower letters
        # decide on data-type:
        if '@' in info:
            _filter = 'email'
        elif info.isalpha():
            _filter = 'nethz'
        else:
            if info[0] is 's':
                info = info.replace('s', '')
            _filter = 'legi'
        # formulate request
        r = self._api_get('/users?where={"%s":"%s"}' % (_filter, info))
        rj = r.json()
        # check for multiple or none entries
        if int(rj['_meta']['total']) > 1:
            raise Exception("More than one user found with {}: {}.".format(_filter, info))
        if int(rj['_meta']['total']) < 1:
            raise Exception("No user found with {}: {}.".format(_filter, info))
        # success! we found exactly one user with the described info. Return it.
        return rj['_items'][0]

    def checkin_field(self, info):
        """ Check in a user to an event by flipping the checked_in value """
        # find user according to info
        user_id = self._get_userinfo_from_info(info)['_id']
        # find the signup with the user
        r = self._api_get('/eventsignups?where={"user":"%s", "event":"%s"}' % (user_id, self.event_id))
        rj = r.json()
        # check numbers of signups
        if int(rj['_meta']['total']) > 1:
            raise Exception("More than one signup found for user: {}.".format(info))
        if int(rj['_meta']['total']) < 1:
            raise Exception("User {} not signed-up for event.".format(info))
        # found exactly one signup
        rj = rj['_items'][0]
        if ('checked_in' in rj) and (rj['checked_in'] is True):
            raise Exception("User {} already checked in.".format(info))
        # create PATCH to check-in user
        esu_id = rj['_id']
        etag = rj['_etag']
        url = self.api_url + '/eventsignups/%s?embedded={"user":1}' % esu_id  # we must target specific eventsignup with id
        header = {'If-Match': etag}
        payload = {"checked_in": "True"}
        r = requests.patch(url, auth=self.auth_obj, headers=header, data=payload)
        if r.status_code != 200:
            raise Exception('Could not check-in user: API responded {}.'.format(r.status_code))
        return self._clean_signup_obj(r.json())

    def checkout_field(self, info):
        """ Check out a user to an event by flipping the checked_in value """
        # find user according to info
        user_id = self._get_userinfo_from_info(info)['_id']
        # find the singup with the user
        r = self._api_get('/eventsignups?where={"user":"%s", "event":"%s"}' % (user_id, self.event_id))
        rj = r.json()
        # check numbers of signups
        if int(rj['_meta']['total']) > 1:
            raise Exception("More than one signup found for user: {}.".format(info))
        if int(rj['_meta']['total']) < 1:
            raise Exception("User {} not signed-up for event.".format(info))
        # found exactly one signup
        rj = rj['_items'][0]
        if 'checked_in' not in rj:
            raise Exception("User {} never checked-in before.".format(info))
        if rj['checked_in'] is None:
            raise Exception("User {} never checked-in before.".format(info))
        if rj['checked_in'] is False:
            raise Exception("User {} already checked out.".format(info))
        # create PATCH to check-out user
        esu_id = rj['_id']
        etag = rj['_etag']
        # we must modify an eventsignup object directly
        url = self.api_url + '/eventsignups/%s?embedded={"user":1}' % esu_id
        header = {'If-Match': etag}
        payload = {"checked_in": "False"}
        r = requests.patch(url, auth=self.auth_obj, headers=header, data=payload)
        if r.status_code != 200:
            raise Exception('Could not check-out user: API responded {}.'.format(r.status_code))
        return self._clean_signup_obj(r.json())

    def checkout_all_remaining(self):
        """ Check-out all remaining checked_in users """
        if self.last_signups is None:
            self.get_signups_for_event()

        for u in self.last_signups:
            if u['checked_in']:
                self.checkout_field(u['email'])

        return True
