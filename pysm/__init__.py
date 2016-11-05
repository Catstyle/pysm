from .state import State, WhateverState
from .event import Event, RestoreEvent
from .handler import state_machine
from .error import InvalidTransition


__all__ = [
    'State', 'WhateverState', 'Event', 'RestoreEvent', 'InvalidTransition',
    'state_machine'
]

__version__ = '0.4.1'
VERSION = tuple(map(int, __version__.split('.')))
