
from .dummy_interface import Dummy_Interface
from .amivapi_interface import AMIV_API_Interface
from .pvkapi_interface import PVK_API_Interface

def create_connectors():
	
	# instantiate interfaces
	If_1 = AMIV_API_Interface()
	If_2 = PVK_API_Interface()
	If_3 = Dummy_Interface()

	# create list and return
	connectors = [If_1, If_2, If_3]
	return connectors

def get_connector_by_id(connectors, idstr):
	for c in connectors:
		if c.id_string == idstr:
			return c

	raise Exception('Could not find connector with id: {}'.format(idstr))
