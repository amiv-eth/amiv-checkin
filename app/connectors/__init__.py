
# id string for gv tool
gvtool_id_string = 'conn_gvtool'
freebies_id_string = 'conn_freebies'


from .dummy_interface import Dummy_Interface
from .amivapi_interface import AMIV_API_Interface
from .gvtool_interface import GV_Tool_Interface
from .pvkapi_interface import PVK_API_Interface
from .freebies_interface import Freebies_Interface


def create_connectors():
    # instantiate interfaces
    if_1 = AMIV_API_Interface()
    #if_2 = PVK_API_Interface()
    if_3 = GV_Tool_Interface()
    #if_4 = Dummy_Interface()
    if_5 = Freebies_Interface()

    # create list and return
    #connectors = [if_1, if_2, if_3, if_4]
    connectors = [if_1, if_3, if_5]
    return connectors


def get_connector_by_id(connectors: list, idstr: str) -> AMIV_API_Interface:
    for c in connectors:
        if c.id_string == idstr:
            return c

    raise Exception('Could not find connector with id: {}'.format(idstr))
