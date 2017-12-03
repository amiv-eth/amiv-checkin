
from .dummy_interface import Dummy_Interface

def create_connectors():
	
	# instantiate interfaces
	D = Dummy_Interface()

	# create list and return
	connectors = [D]
	return connectors

def get_connector_by_id(connectors, idstr):
	for c in connectors:
		if c.id_string == idstr:
			return c

	raise Exception('Could not find connector with id: {}'.format(idstr))
