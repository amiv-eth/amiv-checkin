from .amivapi_interface import AMIV_API_Interface


class Event_Interface(AMIV_API_Interface):
    human_string = "The Event"
    id_string = "conn_theevent"

    def __init__(self):
        super().__init__()

        self.human_string = Event_Interface.human_string
        self.id_string = Event_Interface.id_string
