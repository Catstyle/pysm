__all__ = [
    'State', 'WhateverState', 'Event', 'RestoreEvent', 'InvalidStateTransition',
    'state_machine'
]

__version__ = '0.3.0'
VERSION = tuple(map(int, __version__.split('.')))

from .models import Event, RestoreEvent, State, WhateverState
from .orm import get_adaptor
from .errors import InvalidStateTransition


def state_machine(original_class):
    adaptor = get_adaptor(original_class)
    return adaptor.process_class(original_class)
