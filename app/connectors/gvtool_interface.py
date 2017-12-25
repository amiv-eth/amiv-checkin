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
        ev['spots'] = 0 # GVs are always unlimited
        ev['signup_count'] = len(raw_gv.signups)
        ev['time_start'] = raw_gv.time_start
        ev['description'] = raw_gv.description
        return ev

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
            u = self._api_get('/users/{:s}'.format(s['user_id']))
            s.assign_user(u.json())

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
                total_att = total_att + 1
        stats['Total Members Present'] = stats['Regular Members']\
                                         + stats['Extraordinary Members']\
                                         + stats['Honorary Members']
        stats['Total Attendance'] = total_att

        return stats

    def checkin_field(self, info):
        """ Check in a user to an event by flipping the checked_in value """
        raise Exception('checkin not implemented')

    def checkout_field(self, info):
        """ Check out a user to an event by flipping the checked_in value """
        raise Exception('checkout not implemented')

    '''
    GV Tool Specific Methods
    '''

    def create_new_gv(self, title, time_start, desc=None):
        """ Function to create a new GV with title and description """
        gv = GVEvent(title=title, description=desc, time_start=time_start)
        db.session.add(gv)
        db.session.dommit()
