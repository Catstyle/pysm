__all__ = [
    'State', 'WhateverState', 'Event', 'RestoreEvent', 'InvalidStateTransition',
    'state_machine'
]

__version__ = '0.4.0'
VERSION = tuple(map(int, __version__.split('.')))

from .state import State, WhateverState, state_machine
from .event import Event, RestoreEvent, InvalidStateTransition
