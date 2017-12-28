# global imports
import datetime
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import time

# local imports
from app import db
from .amivapi_interface import AMIV_API_Interface
from .gvtool_models import GVEvent, GVSignup, GVLog
from ..connectors import gvtool_id_string


class GV_Tool_Interface(AMIV_API_Interface):
    """ Interface class to represent GVs with member data from the AMIV API """
    def __init__(self):
        super().__init__()

        self.human_string = "AMIV General Assemblies"
        self.id_string = gvtool_id_string

    def _clean_gv_obj(self, raw_gv):
        """ Re-format the event object from the API to easier, internal representation """
        ev = dict()
        ev['_id'] = str(raw_gv._id)
        ev['title'] = raw_gv.title
        ev['spots'] = 0  # GVs are always unlimited
        ev['signup_count'] = len(raw_gv.signups)
        ev['time_start'] = raw_gv.time_start
        ev['description'] = raw_gv.description
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
            'checked_in': raw_signup.checked_in,
            'legi': legi,
            'membership': user_info['membership'],
            'user_id': user_info['_id'],
            'signup_id': raw_signup._id}

    def get_next_events(self, filter_resp=True):
        """ Fetch all GVs (filter_resp argument has no effect)"""
        return [self._clean_gv_obj(e) for e in GVEvent.query.all()]

    def get_event(self):
        """ Return the event object for the set event_id """
        return self._clean_gv_obj(GVEvent.query.get(self.event_id))

    def get_signups_for_event(self):
        """ Fetch the list of participants for a specific event """
        gv = GVEvent.query.get(self.event_id)

        if len(gv.signups) == 0:
            self.last_signups = []
            return []

        # get pagination information by asking dummy data
        r = self._api_get('/users?&where={"_id": {"$in": ["00000000000000"]}}')
        rj = r.json()
        n_page = rj['_meta']['max_results']

        # split up gv.signups into page-sized sub lists
        gvsu_splits = [gv.signups[j:j+n_page] for j in range(0, len(gv.signups), n_page)]

        # save retrieved users in dict using the users _id as index
        _users = dict()

        def _get_userlist_from_api(sublidx):
            _ids = ','.join(['"' + str(s.user_id) + '"' for s in gvsu_splits[sublidx]])
            _filter = '{"_id": {"$in": [' + _ids + ']}}'
            r = self._api_get('/users?where=%s' % _filter)
            for u in r.json()['_items']:
                _users[u['_id']] = u

        # get all pages of users in parallel
        start = time.time()
        with ThreadPoolExecutor(max_workers=100) as executor:
            u_futures = [executor.submit(_get_userlist_from_api, sublidx) for sublidx in range(len(gvsu_splits))]
            [future.result() for future in u_futures]
        end = time.time()
        print('\n\n\n used time: {:f}\n\n\n'.format(end-start))


        # double check if we got all users
        if len(_users) != len(gv.signups):
            raise Exception('AMIV API did not return the correct amount of users.')

        # attach users to signups
        for s in gv.signups:
            s.set_user(_users[s.user_id])

        # assemble return list
        response = list()
        for esu in gv.signups:
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
        stats['Regular Members'] = 0
        stats['Extraordinary Members'] = 0
        stats['Honorary Members'] = 0
        stats['Total Members Present'] = 0
        stats['Total Non-Members Present'] = 0
        stats['Total Attendance'] = 0
        stats['Maximum Attendance'] = len(self.last_signups)
        total_att = 0

        for u in self.last_signups:
            if u['checked_in'] is True:
                if u['membership'] == self.mem_reg_key:
                    stats['Regular Members'] = stats['Regular Members'] + 1
                elif u['membership'] == self.mem_ext_key:
                    stats['Extraordinary Members'] = stats['Extraordinary Members'] + 1
                elif u['membership'] == self.mem_hon_key:
                    stats['Honorary Members'] = stats['Honorary Members'] + 1
                elif u['membership'] == self.non_mem_key:
                    stats['Total Non-Members Present'] = stats['Total Non-Members Present'] + 1
                else:
                    raise Exception('Unknown membership string.')
                total_att = total_att + 1
        stats['Total Members Present'] = stats['Regular Members']\
                                         + stats['Extraordinary Members']\
                                         + stats['Honorary Members']
        stats['Total Attendance'] = total_att

        return stats

    def _checkin_user_and_log(self, signup, info):
        if (signup.checked_in is None) or (signup.checked_in is False):
            signup.checked_in = True
            signup.logs.append(GVLog(checked_in=True, timestamp=datetime.datetime.now()))
            db.session.commit()
        else:
            raise Exception("User {} already checked in.".format(info))

    def _checkout_user_and_log(self, signup, info):
        if signup.checked_in:
            signup.checked_in = False
            signup.logs.append(GVLog(checked_in=False, timestamp=datetime.datetime.now()))
            db.session.commit()
        elif not signup.checked_in:
            raise Exception("User {} already checked out.".format(info))
        else:
            raise Exception("User {} never checked-in before.".format(info))

    def checkin_field(self, info):
        """ Check in a user to an event by flipping the checked_in value """
        apiuser = self._get_userinfo_from_info(info)
        uid = apiuser['_id']

        # check if user already signed up
        gvsus = GVSignup.query.filter_by(user_id=uid, gvevent_id=self.event_id).all()
        # check numbers of signups
        if len(gvsus) > 1:
            raise Exception("More than one signup found for user: {}.".format(info))
        if len(gvsus) == 1:
            # user already in GV, check-in if needed
            gvsu = gvsus[0]
            self._checkin_user_and_log(gvsu, info)
        if len(gvsus) < 1:
            # user not yet in GV, create new signup, then check-in
            gv = GVEvent.query.get(self.event_id)
            gvsu = GVSignup(user_id=uid)
            gv.signups.append(gvsu)
            self._checkin_user_and_log(gvsu, info)

        # return new signup object
        gvsu.set_user(apiuser)
        return self._clean_signup_obj(gvsu)

    def checkout_field(self, info):
        """ Check out a user to an event by flipping the checked_in value """
        apiuser = self._get_userinfo_from_info(info)
        uid = apiuser['_id']

        # check if user already signed up
        gvsus = GVSignup.query.filter_by(user_id=uid, gvevent_id=self.event_id).all()
        # check numbers of signups
        if len(gvsus) > 1:
            raise Exception("More than one signup found for user: {}.".format(info))
        if len(gvsus) == 1:
            # user already in GV, check-out if needed
            gvsu = gvsus[0]
            self._checkout_user_and_log(gvsu, info)
        if len(gvsus) < 1:
            raise Exception("User {} never checked-in before.".format(info))

        # return new signup object
        gvsu.set_user(apiuser)
        return self._clean_signup_obj(gvsu)

    '''
    GV Tool Specific Methods
    '''

    def create_new_gv(self, title, desc=None):
        """ Function to create a new GV with title and description """
        gv = GVEvent(title=title, description=desc)
        db.session.add(gv)
        db.session.commit()
        return gv

    def get_gv_attendance_log(self):
        """
        Retrieve log of attendance changes for GV
        returns an ordered list of log entry dicts with the following keys:
            timestamp:  datetime of timestamp
            nethz:      nethz name of user
            email:      email of user
            membership: membership status of user
            new_state:  new state of checked_in field (True for in, False for out)
            N_reg_mem:  new number of checked-in regular members
            N_ext_mem:  new number of checked-in extraordinary members
            N_hon_mem:  new number of checked-in honorary member
            N_mem:      new number of total checked-in members
            N_total:    total number of checked-in participants (members and non-members)
        """
        if self.last_signups is None:
            self.get_signups_for_event()

        # query all logs
        gvlogs = GVLog.query\
            .filter(GVSignup.gvevent_id==self.event_id, GVLog.gvsignup_id==GVSignup._id)\
            .order_by(GVLog.timestamp.asc())\
            .all()

        # loop variables
        out_list = list()
        N_reg_mem = 0
        N_ext_mem = 0
        N_hon_mem = 0
        N_non_mem = 0

        # assemble output data
        for gvlog in gvlogs:
            d = OrderedDict()  # we want to remember the insertion order of the keys

            # find user information in stored last_signups list by matching GVSignup._id
            sidx = [i for i, _ in enumerate(self.last_signups) if _['signup_id'] == gvlog.gvsignup_id][0]
            participant = self.last_signups[sidx]

            # count membership
            if gvlog.checked_in:
                op = +1
            else:
                op = -1
            if participant['membership'] == self.mem_reg_key:
                N_reg_mem = N_reg_mem + op
            elif participant['membership'] == self.mem_ext_key:
                N_ext_mem = N_ext_mem + op
            elif participant['membership'] == self.mem_hon_key:
                N_hon_mem = N_hon_mem + op
            elif participant['membership'] == self.non_mem_key:
                N_non_mem = N_non_mem + op
            else:
                raise Exception('Unknown membership string.')

            # output dict per log entry
            d['timestamp'] = gvlog.timestamp
            d['nethz'] = participant['nethz']
            d['email'] = participant['email']
            d['membership'] = participant['membership']
            d['new_state'] = gvlog.checked_in
            d['N_reg_mem'] = N_reg_mem
            d['N_ext_mem'] = N_ext_mem
            d['N_hon_mem'] = N_hon_mem
            d['N_mem'] = N_reg_mem + N_ext_mem + N_hon_mem
            d['N_total'] = N_reg_mem + N_ext_mem + N_hon_mem + N_non_mem

            out_list.append(d)

        # return final list
        return out_list
