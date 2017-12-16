# global imports
import requests

# local imports
from .amivapi_interface import AMIV_API_Interface


class GV_Tool_Interface(AMIV_API_Interface):
    """ Interface class to represent GVs with member data from the AMIV API """
    def __init__(self):
        super().__init__()

        self.human_string = "AMIV General Assemblies"
        self.id_string = "conn_gvtool"

    def get_next_events(self):
        """ Fetch the upcoming events between today and tomorrow """
        pass

    def get_signups_for_event(self):
        """ Fetch the list of participants for a specific event """
        pass

    def get_statistics(self):
        """ return the statistics string for the last fetched  """
        pass

    def checkin_field(self, info):
        """ Check in a user to an event by flipping the checked_in value """
        pass

    def checkout_field(self, info):
        """ Check out a user to an event by flipping the checked_in value """
        pass
