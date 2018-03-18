from datetime import datetime, timedelta
import requests


class PVK_API_Interface:
    """ Interface class to fetch and update data through the PVK API """
    def __init__(self):

        raise Exception("Do not use this class. It is not maintained.")

        self.amiv_api_url = "https://amiv-api.ethz.ch"
        self.api_url = ""  # TODO: Add URL of PVK API
        self.datetime_format = "%Y-%m-%dT%H:%M:%SZ"

        self.token = ""
        self.auth_obj = ""

        self.human_string = "AMIV PVK Courses"
        self.id_string = "conn_pvkapi"

    def login(self, username, password):
        """ Log in the user to obtain usable token for requests """
        payload = {"user": str(username), "password": password}
        r = requests.post(self.amiv_api_url + '/sessions', data=payload)
        if r.status_code is 201:
            self.token = r.json()['token']
            self.auth_obj = requests.auth.HTTPBasicAuth(self.token, "")

    def get_next_events(self):
        """ Fetch the upcoming courses between today and today+100 """
        low_bound = datetime.today().strftime(self.datetime_format)
        up_bound = datetime.today() + timedelta(days=100)
        up_bound = up_bound.strftime(self.datetime_format)
        # TODO: Fix range setting to use datetimes list
        _range = '{"time_start":{"$gt":"'+low_bound+'","$lt":"'+up_bound+'"}}'
        r = requests.get(self.api_url + '/courses?where=' + _range)
        return r.json()

    def get_signups_for_event(self, course_id):
        """ Fetch the list of participants for a specific course """
        _filter = '/signups?where={"course":"%s"}' % course_id
        r = requests.get(self.api_url + _filter, auth=self.auth_obj)
        return r.json()

    def set_event(self, course_id):
        """ Set the event_id for this instance of the class """
        self.course_id = course_id

    def _get_userid_from_legi(self, legi):
        """ Fetch the user_id from a legi number """
        _filter = '/users?where={"legi":"%s"}' % legi
        r = requests.get(self.amiv_api_url + _filter,
                         auth=self.auth_obj)
        if r.status_code is 200:
            return r.json()['nethz']
        return "Error: No user found"

    def _get_userid_from_nethz(self, nethz):
        """ Fetch the user_id from a nethz username """
        _filter = '/users?where={"nethz":"%s"}' % nethz
        r = requests.get(self.amiv_api_url + _filter,
                         auth=self.auth_obj)
        if r.status_code is 200:
            return r.json()['nethz']
        return "Error: No user found"

    def _get_userid_from_email(self, email):
        """ Fetch the user_id from a mail adress """
        _filter = '/users?where={"email":"%s"}' % email
        r = requests.get(self.amiv_api_url + _filter,
                         auth=self.auth_obj)
        if r.status_code is 200:
            if len(r.json().keys()) is 1:
                return r.json()['nethz']
        return "Error: Multiple entries found or no user found"

    def _get_userid_from_info(self, info):
        """ Choose the function to use to fetch the u_id """
        if '@' in info:
            user_id = self._get_userid_from_email(info)
        elif info.isalpha():
            # user_id = self._get_userid_from_nethz(info)
            user_id = info
        else:
            if info[0] is 'S':
                info.replace('S', '')
            user_id = self._get_userid_from_legi(info)
        return user_id

    def get_headers_filter_url(self,info):
        user_id = self._get_userid_from_info(info)
        if 'Error' in user_id:
            return False
        _filter = ('?where={"nethz":"%s", "course":"%s"}'
                   % user_id, self.course_id)
        r = requests.get(self.api_url + '/signups' + _filter,
                         auth=self.auth_obj)
        if r.status_code != 200:
            return False
        etag = r.json()['_etag']
        url = self.api_url + '/signups'
        header = {'If-Match': etag}

        return header, _filter, url

    def checkin_field(self, info):
        """ Check in a user to a course by flipping the checked_in value """
        header, _filter, url = self.get_headers_filter_url(info)

        payload = {"checked_in": "True"}
        r = requests.patch(url + _filter,
                           auth=self.auth_obj,
                           headers=header,
                           data=payload)
        return r.status_code == 200

    def checkout_field(self, info):
        """ Check in a user to an event by flipping the checked_in value """
        header, _filter, url = self.get_headers_filter_url(info)

        payload = {"checked_in": "False"}
        r = requests.patch(url + _filter,
                           auth=self.auth_obj,
                           headers=header,
                           data=payload)
        return r.status_code == 200
