# global imports
import datetime
from copy import deepcopy

# local imports
from app import db
from .amivapi_interface import AMIV_API_Interface
from .gvtool_models import GVEvent, GVSignup, GVLog


class GV_Tool_Interface(AMIV_API_Interface):
    """ Interface class to represent GVs with member data from the AMIV API """
    def __init__(self):
        super().__init__()

        self.human_string = "AMIV General Assemblies"
        self.id_string = "conn_gvtool"

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
            '_id': user_info['_id']}

    def get_next_events(self, filter_resp=True):
        """ Fetch all GVs (filter_resp argument has no effect)"""
        return [self._clean_gv_obj(e) for e in GVEvent.query.all()]

    def get_event(self):
        """ Return the event object for the set event_id """
        return self._clean_gv_obj(GVEvent.query.get(self.event_id))

    def get_signups_for_event(self):
        """ Fetch the list of participants for a specific event """
        gv = GVEvent.query.get(self.event_id)

        # fetch user information from AMIV API
        # WARNING: THIS PRODUCES ONE REQUEST PER USER! REWRITE FOR SPEED REQUIRED.
        for s in gv.signups:
            u = self._api_get('/users/{:s}'.format(s.user_id))
            s.set_user(u.json())

        # assemble return list
        response = list()
        for esu in gv.signups:
            response.append(self._clean_signup_obj(esu))

        # safe this for get_statistics
        self.last_signups = deepcopy(response)

        return response

    def get_statistics(self):
        """ return the statistics string for the last fetched  """
        if self.last_signups is None:
            return {}

        stats = {
            'Regular Members': 0,
            'Extraordinary Members': 0,
            'Honorary Members': 0,
            'Total Members Present': 0,
            'Total Non-Members Present': 0,
            'Total Attendance': 0,
            'Maximum Attendance': len(self.last_signups)
        }
        total_att = 0
        for u in self.last_signups:
            if u['checked_in'] is True:
                if u['membership'] == 'regular':
                    stats['Regular Members'] = stats['Regular Members'] + 1
                elif u['membership'] == 'extraordinary':
                    stats['Extraordinary Members'] = stats['Extraordinary Members'] + 1
                elif u['membership'] == 'honorary':
                    stats['Honorary Members'] = stats['Honorary Members'] + 1
                elif u['membership'] == 'none':
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
            signup.logs.append(GVLog(checked_in=True))
            db.session.commit()
        else:
            raise Exception("User {} already checked in.".format(info))

    def _checkout_user_and_log(self, signup, info):
        if signup.checked_in:
            signup.checked_in = False
            signup.logs.append(GVLog(checked_in=False))
            db.session.commit()
        elif not signup.checked_in:
            raise Exception("User {} already checked out.".format(info))
        else:
            raise Exception("User {} never checked-in before.".format(info))

    def checkin_field(self, info):
        """ Check in a user to an event by flipping the checked_in value """
        uid = self._get_userinfo_from_info(info)['_id']

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

        return True

    def checkout_field(self, info):
        """ Check out a user to an event by flipping the checked_in value """
        uid = self._get_userinfo_from_info(info)['_id']

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

        return True

    '''
    GV Tool Specific Methods
    '''

    def create_new_gv(self, title, desc=None):
        """ Function to create a new GV with title and description """
        gv = GVEvent(title=title, description=desc)
        db.session.add(gv)
        db.session.commit()
        return gv
