from collections import OrderedDict
from datetime import datetime, timedelta
import requests
import re
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

        self.legi_regex = re.compile("[sS]?[0-9]{8}")

        self.minimum_permissions = {
            'users': 'read',
            'eventsignups': 'readwrite'
        }
        # 'events': 'read',  # any logged in user has this anyway and this permission need not to be checked here

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
        # get all groups of the user and embed their details to get permission information
        uid = rj['user']
        _filter = '{"user":"%s"}' % uid
        _memberships = self._api_get_all_items('/groupmemberships',
                                               'where=' + _filter + '&embedded={"group":1}')
        # get this users group-based permissions
        users_permissions = {}
        for ms in _memberships:
            # skip all groups which do not have permissions fixed or which do not exist anymore
            if ('group' not in ms) or (ms['group'] is None) or ('permissions' not in ms['group']):
                continue
            # then we go through all permissions and save them
            for k, v in ms['group']['permissions'].items():
                if k in users_permissions:
                    # overwrite permission only if we have write in it (i.e. it's more powerful)
                    if 'write' in v:
                        users_permissions[k] = v
                else:
                    # store new permission
                    users_permissions[k] = v

        # check if the user has the required permissions and give exact error messages
        for p_name, p_level in self.minimum_permissions.items():
            if p_name not in users_permissions:
                raise Exception("API user {:s} does not have the '{:s}':'{:s}' permission in any of his groups.".format(
                    username,
                    p_name,
                    p_level))
            if p_level not in users_permissions[p_name]:
                raise Exception("API user's {:s} permission '{:s}':'{:s}' does not have the required level of '{:s}' "
                                "in any of his groups.".format(
                    username,
                    p_name,
                    users_permissions[p_name],
                    p_level
                ))
        # all
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

    def _api_get_all_items(self, url, options):
        """ When getting multiple items, this method retrieves all items from all pages """
        rj = self._api_get(str(url) + '?' + str(options)).json()
        _items = [x for x in rj['_items']]
        # get information how many items there are in total and how many items are on one page
        ntotal = rj['_meta']['total']
        npage = rj['_meta']['max_results']
        # execute the get request for all other pages
        for p in range(2, int(ceil(ntotal / npage)) + 1):
            r = self._api_get(url + '?page={:d}&'.format(p) + str(options))
            _items.extend(r.json()['_items'])
        # double check if we got all items and return
        assert len(_items) == ntotal, 'Number of items retrieved ({:d}) does not match APIs total value ({:d}).'.format(
            len(_items),
            ntotal
        )
        return _items

    def _clean_event_obj(self, raw_event):
        """ Re-format the event object from the API to easier, internal representation """
        ev = dict()
        ev['_id'] = str(raw_event['_id'])
        if 'title_en' in raw_event and raw_event['title_en']:
            ev['title'] = raw_event['title_en']
        else:
            ev['title'] = raw_event['title_de']
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
        if 'user' in raw_signup:
            user_info = raw_signup['user']
        else:
            # unregistered user signup with email only
            # the email field is stored in the signup object
            user_info = {'email': raw_signup['email']}

        # assemble signup dict
        return {
            'firstname': user_info.get('firstname', '*Unregistered*'),
            'lastname': user_info.get('lastname', '*User*'),
            'nethz': user_info.get('nethz'),
            'email': user_info.get('email'),
            'checked_in': raw_signup.get('checked_in'),
            'legi': user_info.get('legi'),
            'membership': user_info.get('membership', 'none'),
            'user_id': user_info.get('_id'),
            'signup_id': raw_signup.get('_id')}

    def get_next_events(self, filter_resp=True):
        """ Fetch the upcoming events between today and tomorrow """
        if (app is not None) and (app.debug is False):
            low_bound = datetime.today() - timedelta(days=2)
            low_bound = low_bound.strftime(self.datetime_format)
            up_bound = datetime.today() + timedelta(days=100)
            up_bound = up_bound.strftime(self.datetime_format)
            _range = '{"time_start":{"$gt":"' + low_bound + '","$lt":"' + up_bound + '"}, "spots":{"$gte":0}}'
        else:
            # debug case: do not filter for time, just display all
            _range = '{"spots":{"$gte":0}}'

        _events = self._api_get_all_items('/events',
                                          'where=' + _range)

        if len(_events) is 0:
            raise Exception("No Events found in the next 100 days.")

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

        _signups = self._api_get_all_items('/eventsignups',
                                           'where={"event":"%s"}&embedded={"user":1}' % self.event_id)

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
        stats['Total Signups'] = len(self.last_signups)
        for u in self.last_signups:
            if u['checked_in'] is True:
                stats['Current Attendance'] = stats['Current Attendance'] + 1

        return stats

    def _get_userinfo_from_info(self, info):
        """ Choose the function to use to fetch the u_id """
        info = info.strip().lower()  # get rid of whitespace and make everything lower letters
        # decide on data-type:
        if '@' in info:
            _filter = 'email'
        elif self.legi_regex.match(info):
            if info[0] is 's':
                info = info.replace('s', '')
            _filter = 'legi'
        else:
            _filter = 'nethz'
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
        info = str(info).strip().lower()  # get rid of whitespace and make everything lower letters

        num_anonymous = 0
        if '@' in info:
            # there is an email in info, check the email field for all the anonymous, email only signups
            r = self._api_get('/eventsignups?where={"email":"%s", "event":"%s"}' % (info, self.event_id))
            rj = r.json()
            num_anonymous = int(rj['_meta']['total'])

        # in case it is not an email or the anonymous search did not produce any result, look for other user info
        if ('@' not in info) or (num_anonymous < 1):
            user_id = self._get_userinfo_from_info(info)['_id']
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
        # we must target specific eventsignup with id in request
        url = self.api_url + '/eventsignups/%s?embedded={"user":1}' % esu_id
        header = {'If-Match': etag}
        payload = {"checked_in": "True"}
        r = requests.patch(url, auth=self.auth_obj, headers=header, data=payload)
        if r.status_code != 200:
            raise Exception('Could not check-in user: API error {}.'.format(r.status_code))

        su = self._clean_signup_obj(r.json())
        return {'message': '{:s} member checked-IN!'.format(su['membership'].upper()), 'signup': su}

    def checkout_field(self, info):
        """ Check out a user to an event by flipping the checked_in value """
        info = str(info).strip().lower()  # get rid of whitespace and make everything lower letters

        num_anonymous = 0
        if '@' in info:
            # there is an email in info, check the email field for all the anonymous, email only signups
            r = self._api_get('/eventsignups?where={"email":"%s", "event":"%s"}' % (info, self.event_id))
            rj = r.json()
            num_anonymous = int(rj['_meta']['total'])

        # in case it is not an email or the anonymous search did not produce any result, look for other user info
        if ('@' not in info) or (num_anonymous < 1):
            user_id = self._get_userinfo_from_info(info)['_id']
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

        su = self._clean_signup_obj(r.json())
        return {'message': '{:s} member checked-OUT!'.format(su['membership'].upper()), 'signup': su}

    def checkout_all_remaining(self):
        """ Check-out all remaining checked_in users """
        if self.last_signups is None:
            self.get_signups_for_event()

        for u in self.last_signups:
            if u['checked_in']:
                self.checkout_field(u['email'])

        return True
