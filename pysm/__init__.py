from .state import State, WhateverState
from .event import Event, InstanceEvent
from .handler import state_machine


__all__ = ['state_machine', 'State', 'WhateverState', 'Event', 'InstanceEvent']

__version__ = '0.4.1'
VERSION = tuple(map(int, __version__.split('.')))
