from .amivapi_interface import AMIV_API_Interface

from datetime import datetime

from .event_models import EventCount
from .. import db


class Event_Interface(AMIV_API_Interface):
    human_string = "The Event"
    id_string = "conn_theevent"

    def __init__(self):
        super().__init__()

        self.human_string = Event_Interface.human_string
        self.id_string = Event_Interface.id_string

    def get_event(self):
        """ Return the event object for the set event_id """
        r = self._api_get('/events/{}'.format(self.event_id))
        return self._clean_event_obj(r.json())

    def _clean_event_obj(self, raw_event):
        """ Re-format the event object from the API to easier, internal representation """

        ev = dict()
        for k in raw_event:
            ev[k] = raw_event[k]
        ev['_id'] = str(raw_event['_id'])
        if 'title_en' in raw_event and raw_event['title_en']:
            ev['title'] = raw_event['title_en']
        else:
            ev['title'] = raw_event['title_de']
        if 'time_start' in raw_event:
            ev['time_start'] = datetime.strptime(raw_event['time_start'],
                                                 self.datetime_format)
        return ev

    def count_increment(self, info, signup_needed, maxcount):
        user_id = self._get_userinfo_from_info(info)['_id']

        if signup_needed:
            # find the signup with the user
            r = self._api_get(
                '/eventsignups?where={"user":"%s", "event":"%s"}' % (
                    user_id, self.event_id))
            rj = r.json()

            if int(rj['_meta']['total']) == 0:
                raise Exception("User {} not signed-up for event.".format(
                    info))

        # Now add count to the local database
        event_counts = EventCount.query.filter_by(
            event_id=self.event_id, user_id=user_id).all()

        if len(event_counts) == 0:
            db.session.add(EventCount(
                event_id=self.event_id, user_id=user_id, count=1))
            db.session.commit()
            return 1

        elif len(event_counts) > 1:
            raise Exception(
                "Data error on counts for user {} on event {}".format(
                    user_id, self.event_id))

        else:
            event_count = event_counts[0]
            if event_count.count > maxcount-1:
                raise Exception(
                    "User {} reached event count limit.".format(
                        info))

            event_count.count += 1
            db.session.commit()
            return event_count.count

    def get_attendee_counts(self):
        """ Fetch the list of participants for a specific event """

        attendee_counts = []

        event_counts = EventCount.query.filter_by(event_id=self.event_id).all()

        for ec in event_counts:
            r = self._api_get('/users?where={"_id":"%s"}' % ec.user_id)
            r = r.json()['_items'][0]
            r = {'firstname': r['firstname'],
                 'lastname': r['lastname'],
                 'nethz': r['nethz'],
                 'email': r['email'],
                 'legi': r['legi'],
                 'membership': r['membership'],
                 'user_id': ec.user_id}

            attendee_counts.append((r, ec.count))

        return attendee_counts
