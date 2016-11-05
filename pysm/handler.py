import inspect
from functools import partial

from .state import State, WhateverState
from .event import Event, RestoreEvent
from .error import InvalidEventState


def validate_states(event):
    for state in event.from_states + (event.to_state,):
        if not inspect.isclass(state) or not issubclass(state, State):
            raise InvalidEventState('%s is not inherit from `State`' % state)


def attach_state(instance, state):
    assert instance.current_state is None
    base_dict = instance.__dict__
    for name, method in state.state_methods.items():
        base_dict[name] = partial(method, instance)
        instance._pysm_state_methods.add(name)
    instance.current_state = state


def detach_state(instance):
    assert instance.current_state
    base_dict = instance.__dict__
    for name in instance._pysm_state_methods:
        base_dict.pop(name, None)
    instance._pysm_state_methods.clear()
    instance.current_state = None


def switch_state(instance, from_state, to_state, *args, **kwargs):
    instance.exit_state(to_state)
    detach_state(instance)
    instance._pysm_previous_state = from_state
    attach_state(instance, to_state)
    instance.enter_state(from_state, *args, **kwargs)


def state_machine(original_class):
    process_states(original_class)
    process_events(original_class)

    original_init = original_class.__init__

    def new_init(self, *args, **kwargs):
        self._pysm_state_methods = set()
        self._pysm_previous_state = None
        self.current_state = None
        attach_state(self, self._pysm_initial_state)
        original_init(self, *args, **kwargs)
    original_class.__init__ = new_init
    return original_class


def process_states(original_class):
    original_class._pysm_initial_state = None
    original_class._pysm_states = {}
    for name, value in inspect.getmembers(original_class):
        if not (inspect.isclass(value) and issubclass(value, State)):
            continue
        if issubclass(value, WhateverState):
            raise TypeError('cannot inherit from WhateverState')

        original_class._pysm_states[name] = value
        if getattr(value, 'initial', False):
            if original_class._pysm_initial_state is not None:
                raise ValueError("multiple initial states!")
            original_class._pysm_initial_state = value

    if original_class._pysm_initial_state is None:
        raise ValueError('missing initial state')


def process_events(original_class):
    original_class._pysm_events = {}
    for name, value in inspect.getmembers(original_class):
        if not isinstance(value, Event):
            continue
        validate_states(value)
        value.name = name
        original_class._pysm_events[name] = value

        if isinstance(value, RestoreEvent):
            restore_name = 'restore_from_' + name
            restore_event = Event(
                from_states=value.to_state, to_state=WhateverState
            )
            restore_event.name = restore_name
            setattr(original_class, restore_name, restore_event)
            original_class._pysm_events[restore_name] = restore_event
