# global imports
import datetime
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

# local imports
from math import ceil

from app import db
from .amivapi_interface import AMIV_API_Interface
from .freebies_models import FreebieEvent, FreebieSignup, FreebieLog
from ..connectors import freebies_id_string


class Freebies_Interface(AMIV_API_Interface):
    """ Interface class to represent Freebie Events with member data from the AMIV API """
    def __init__(self):
        super().__init__()

        self.human_string = "AMIV Freebies"
        self.id_string = freebies_id_string

    def _clean_freebie_obj(self, raw_obj):
        """ Re-format the event object from the API to easier, internal representation """
        ev = dict()
        ev['_id'] = str(raw_obj._id)
        ev['title'] = raw_obj.title
        ev['spots'] = 0  # GVs are always unlimited
        ev['signup_count'] = len(raw_obj.signups)
        ev['time_start'] = raw_obj.time_start
        ev['description'] = raw_obj.description
        ev['max_freebies'] = raw_obj.max_freebies
        return ev

    def _clean_signup_obj(self, raw_signup):
        user_info = raw_signup.get_user()
        # translate non-existing value to None (these values are optional in API)
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
            'freebies_taken': raw_signup.freebies_taken,
            'legi': legi,
            'membership': user_info['membership'],
            'user_id': user_info['_id'],
            'signup_id': raw_signup._id}

    def get_next_events(self, filter_resp=True):
        """ Fetch all Events (filter_resp argument has no effect)"""
        return [self._clean_freebie_obj(e) for e in FreebieEvent.query.all()]

    def get_event(self):
        """ Return the event object for the set event_id """
        return self._clean_freebie_obj(FreebieEvent.query.get(self.event_id))

    def get_signups_for_event(self):
        """ Fetch the list of participants for a specific event """
        fbev = FreebieEvent.query.get(self.event_id)

        if len(fbev.signups) == 0:
            self.last_signups = []
            return []

        # get pagination information by asking dummy data
        r = self._api_get('/users?&where={"_id": {"$in": ["00000000000000"]}}')
        rj = r.json()
        n_page = rj['_meta']['max_results']

        # split up gv.signups into page-sized sub lists
        fbsu_splits = [fbev.signups[j:j+n_page] for j in range(0, len(fbev.signups), n_page)]

        # save retrieved users in dict using the users _id as index
        _users = dict()

        # request users for page-sized parts of gv.sublist in parallel
        def _get_userlist_from_api(sublidx):
            _ids = ','.join(['"' + str(s.user_id) + '"' for s in fbsu_splits[sublidx]])
            _filter = '{"_id": {"$in": [' + _ids + ']}}'
            r = self._api_get('/users?where=%s' % _filter)
            for u in r.json()['_items']:
                _users[u['_id']] = u

        # get all pages of users in parallel
        with ThreadPoolExecutor(max_workers=100) as executor:
            u_futures = [executor.submit(_get_userlist_from_api, sublidx) for sublidx in range(len(fbsu_splits))]
            [future.result() for future in u_futures]

        # double check if we got all users
        if len(_users) != len(fbev.signups):
            raise Exception('AMIV API did not return the correct amount of users.')

        # attach users to signups
        for s in fbev.signups:
            s.set_user(_users[s.user_id])

        # assemble return list
        response = list()
        for esu in fbev.signups:
            response.append(self._clean_signup_obj(esu))

        # safe this for get_statistics or get_gv_attendance_log
        self.last_signups = deepcopy(response)

        # return final list of dicts
        return response

    def get_statistics(self):
        """ return the statistics string for the last fetched  """
        if self.last_signups is None:
            self.get_signups_for_event()

        stats = OrderedDict()
        stats['Members in list'] = len(self.last_signups)
        stats['Total Freebies taken'] = 0

        for u in self.last_signups:
            stats['Total Freebies taken'] = stats['Total Freebies taken'] + u['freebies_taken']

        return stats

    def checkin_field(self, info):
        """ Register Freebie given to AMIV member """
        apiuser = self._get_userinfo_from_info(info)
        uid = apiuser['_id']

        # check if user already in list
        fbsus = FreebieSignup.query.filter_by(user_id=uid, freebieevent_id=self.event_id).all()
        # check numbers of signups
        if len(fbsus) > 1:
            raise Exception("Member {} is registered more than once in database.".format(info))
        if len(fbsus) == 1:
            # user registered, add freebie if not yet over limit
            fbsu = fbsus[0]
            if (fbsu.freebies_taken is not None) and (fbsu.freebies_taken >= fbsu.FreebieEvent.max_freebies):
                raise Exception('Member reached maximum Freebies!')
            fbsu.freebies_taken = fbsu.freebies_taken + 1
            db.Session.commit()
        if len(fbsus) < 1:
            # user not yet in event, create new signup, then register one freebie taken
            fe = FreebieEvent.query.get(self.event_id)
            fbsu = FreebieSignup(user_id=uid)
            fbsu.freebies_taken = 1
            fe.signups.append(fbsu)
            db.Session.commit()

        # return new signup object
        fbsu.set_user(apiuser)
        return self._clean_signup_obj(fbsu)

    def checkout_field(self, info):
        """ Register Freebie taken back from AMIV member """
        apiuser = self._get_userinfo_from_info(info)
        uid = apiuser['_id']

        # check if user already signed up
        fbsus = FreebieSignup.query.filter_by(user_id=uid, freebieevent_id=self.event_id).all()
        # check numbers of signups
        if len(fbsus) > 1:
            raise Exception("Member {} is registered more than once in database.".format(info))
        if len(fbsus) == 1:
            # user already in GV, take freebie back if larger than 0
            fbsu = fbsus[0]
            if (fbsu.freebies_taken is not None) and (fbsu.freebies_taken > 0):
                fbsu.freebies_taken = fbsu.freebies_taken - 1
            else:
                raise Exception('Member already at 0 Freebies taken.')
            db.Session.commit()
        if len(fbsus) < 1:
            raise Exception("Member {} did not yet get a Freebie.".format(info))

        # return new signup object
        fbsu.set_user(apiuser)
        return self._clean_signup_obj(fbsu)

    '''
    Freebie Tool Specific Methods
    '''

    def create_new_freebies(self, title, desc=None, max_freebies=None):
        """ Function to create a new GV with title and description """
        obj = FreebieEvent(title=title, description=desc, max_freebies=max_freebies)
        db.session.add(obj)
        db.session.commit()
        return obj

