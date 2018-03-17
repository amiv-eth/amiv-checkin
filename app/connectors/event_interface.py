from .amivapi_interface import AMIV_API_Interface

from datetime import datetime


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
            ev['time_start'] = datetime.strptime(raw_event['time_start'], self.datetime_format)
        return ev
