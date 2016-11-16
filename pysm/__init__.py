from .state import State, WhateverState
from .event import Event, InstanceEvent
from .handler import state_machine
from .error import InvalidTransition


__all__ = [
    'state_machine', 'State', 'WhateverState', 'Event', 'InstanceEvent',
    'InvalidTransition'
]

__version__ = '0.4.1'
VERSION = tuple(map(int, __version__.split('.')))
