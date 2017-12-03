
class Dummy_Interface:
    """ Interface class to fetch and update data through the AMIV API """
    def __init__(self):
        self.dummy_users = [
            {'id': '1', 'bn': 'user1', 'pw': 'pw1'}, 
            {'id': '2', 'bn': 'user2', 'pw': 'pw2'}, 
            {'id': '3', 'bn': 'user3', 'pw': 'pw3'}, 
            {'id': '4', 'bn': 'user4', 'pw': 'pw4'}
        ]
        self.dummy_events = [
            {'id': '1', 'title': 'event1', 'spots': 61, 'signup_count': 41, 'time_start': '2017-12-02T19:01:00Z'},
            {'id': '2', 'title': 'event2', 'spots': 62, 'signup_count': 42, 'time_start': '2017-12-02T19:02:00Z'},
            {'id': '3', 'title': 'event3', 'spots': 63, 'signup_count': 43, 'time_start': '2017-12-02T19:03:00Z'},
            {'id': '4', 'title': 'event4', 'spots': 64, 'signup_count': 44, 'time_start': '2017-12-02T19:04:00Z'}
        ]
        self.dummy_eventsignups = [
            #EID, UID
            ('1', '1', False),
            ('2', '1', False), ('2', '2', False),
            ('3', '1', False), ('3', '2', False), ('3', '3', False),
            ('4', '1', False), ('4', '2', False), ('4', '3', False), ('4', '4', False)
        ]

        self.human_string = "Dummy Events"
        self.id_string = "conn_dummy"

    def login(self, username, password):
        """ Log in the user to obtain usable token for requests """
        for u in self.dummy_users:
            if u['bn'] == username and u['pw'] == password:
                # dummy token
                return username+password
        return None

    def get_next_events(self, token):
        """ Fetch the upcoming events between today and tomorrow """
        return self.dummy_events

    def get_signups_for_event(self, token, event_id):
        """ Fetch the list of participants for a specific event """
        ulid = []
        for idx in range(len(self.dummy_eventsignups)):
            if self.dummy_eventsignups[idx][0] == event_id:
                ulid.append(self.dummy_eventsignups[idx])
        ul = []
        for ulidi in ulid:
            for u in self.dummy_users:
                if u['id'] == ulidi:
                    ul.append(u)
        signups = []
        for u in ul:
            signups.append({'name': 'name-'+u['bn'],
                'nethz': 'nethz-'+u['bn'],
                'legi': 'legi-'+u['bn'], 
                'email': 'email-'+u['bn'], 
                'status': 'status-'+u['bn'] })
        return signups

    def checkin_field(self, token, user_id, event_id):
        """ Check in a user to an event by flipping the checked_in valuei """
        for idx in range(self.dummy_eventsignups):
            if self.dummy_eventsignups[idx][0] == event_id:
                if self.dummy_eventsignups[idx][1] == user_id:
                    self.dummy_eventsignups[idx][2] = not self.dummy_eventsignups[idx][2];
        return True
