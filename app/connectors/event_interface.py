from .amivapi_interface import AMIV_API_Interface

class Event_Interface(AMIV_API_Interface):
    def __init__(self):
        super().__init__()

        self.human_string = "The Event"
        self.id_string = "conn_theevent"
