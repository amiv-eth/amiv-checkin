
class Dummy_Interface:
    """ Interface class to fetch and update data through the AMIV API """
    def __init__(self):
        """
        Every connector needs the two following strings:
        """
        self.human_string = "Dummy Events" # Describe for what kind of Events this connector is used
        self.id_string = "conn_dummy"      # give it an ID string

        # These internals are also mandatory
        self.token = ""
        self.event_id = ""

        # dummy-connector internals
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
            #EID, UID, checkin flag
            ('1', '1', False),
            ('2', '1', True),  ('2', '2', False),
            ('3', '1', False), ('3', '2', True),  ('3', '3', False),
            ('4', '1', None),  ('4', '2', None), ('4', '3', None),  ('4', '4', None)
        ]

    def login(self, username, password):
        """ Log in the user to obtain usable token for requests
        
        marcoep: logs the user into the provided API with username / password
        on success: returns a token for the logged-in session
        on failure: raises Exception with descriptive message
        """
        for u in self.dummy_users:
            if u['bn'] == username and u['pw'] == password:
                return username+password # dummy token
        raise Exception('Invalid username or password.')

    def set_token(self, token):
        """
        marcoep: instead of loggin in, we should also be able to provide this class
                 with an already saved token from a previous session
        """
        self.token = token

    def get_next_events(self):
        """ Fetch the upcoming events between today and tomorrow

        marcoep: This function should return a list of dicts.
        Every dict represents one event and has the following keys:
        'id'            - the event id, string(128)
        'title'         - the human readable title of the event, string(128)
        'spots'         - how many sign-up spots are there, integer
        'signup_count'  - how many people have signed up, integer
        'time_start'    - time when the event will start, YYYY-MM-DDTHH:mm:ssZ like string
        """
        return self.dummy_events

    def set_event(self, event_id):
        """
        marcoep: when we have chosen an event to do signups for, use this function
                 to specify its id for further usage
        """
        self.event_id = event_id

    def get_signups_for_event(self):
        """ Fetch the list of participants for a specific event

        marcoep: this function should return a list of dicts.
        Every dict represents one participant of the event self.event_id and 
        has the following keys:
        'name'      - the human readable first and surname of the participant, string
        'nethz'     - the "ETH Kürzel" of the participant, string
        'legi'      - the Legi number of the participant, string
        'email'     - the e-mail address of the participant, string
        'status'    - a boolean value:
            True    if participant is checked in
            False   if participant was here but was checked out
            None    if no check-in / check-out has been registered for participant
        """
        signups = []
        for idx in range(len(self.dummy_eventsignups)):
            if self.dummy_eventsignups[idx][0] == self.event_id:
                for u in self.dummy_users:
                    if u['id'] == self.dummy_eventsignups[idx][1]:
                        signups.append({'name': 'name-'+u['bn'],
                                        'nethz': 'nethz-'+u['bn'],
                                        'legi': 'legi-'+u['bn'], 
                                        'email': 'email-'+u['bn'], 
                                        'status': self.self.dummy_eventsignups[idx][2] })
        return signups

    def checkin_field(self, info):
        """ Check-in user which can be uniquely identified with the info string
        
        marcoep: try to check-in a participant of the event self.event_id. The participant's
        identification is given by the info string. 
        The info string can be:
        - Legi number (with or without starting S)
        - nethz Kürzel
        - email-address

        If any error happens (e.g. participant not in event, participant not found, multiple
        participants found, participant already checked-in, ...) you should raise an Exception
        with a descriptive error message.

        This function should return True if check-in succeeded.
        """

        # search all users for given info
        ul = []
        for u in self.dummy_users:
            if u['bn'] == info:
                ul.append(u)

        # give meaningful output
        if len(ul) > 1:
            raise Exception('More than one user found for {}'.format(info))
        if len(ul) == 0:
            raise Exception('No user found for {}'.format(info))

        # we found user
        uid = ul[0]

        # search correct event signup
        for es in self.dummy_eventsignups:
            if es[0] == self.event_id and es[1] == uid:
                evsig = es
                break

        # check if user is already checked in:
        if evsig[2] == True:
            raise Exception('User already checked-in!')

        # here would come the checkin of the user (not done in dummy class)
        #evsig[2] = True

        return True

    def checkout_field(self, info):
        """ Check-out user which can be uniquely identified with the info string
        
        marcoep: try to check-out a participant of the event self.event_id. The participant's
        identification is given by the info string. 
        The info string can be:
        - Legi number (with or without starting S)
        - nethz Kürzel
        - email-address

        If any error happens (e.g. participant not in event, participant not found, multiple
        participants found, participant not checked-in, ...) you should raise an Exception
        with a descriptive error message.

        This function should return True if check-out succeeded.
        """

        # search all users for given info
        ul = []
        for u in self.dummy_users:
            if u['bn'] == info:
                ul.append(u)

        # give meaningful output
        if len(ul) > 1:
            raise Exception('More than one user found for {}'.format(info))
        if len(ul) == 0:
            raise Exception('No user found for {}'.format(info))

        # we found user
        uid = ul[0]

        # search correct event signup
        for es in self.dummy_eventsignups:
            if es[0] == self.event_id and es[1] == uid:
                evsig = es
                break

        # check if user not checked in:
        if evsig[2] is None or evsig[2] == False:
            raise Exception('User not checked-in!')

        # here would come the checkout of the user (not done in dummy class)
        #evsig[2] = False
        
        return True
