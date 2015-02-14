__version__ = '0.2.1'
VERSION = tuple(map(int, __version__.split('.')))


from pysm.models import Event, RestoreEvent, State, WhateverState
from pysm.orm import get_adaptor
from pysm.errors import InvalidStateTransition


def state_machine(original_class):
    adaptor = get_adaptor(original_class)
    return adaptor.process_class(original_class)
