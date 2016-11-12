import inspect
from functools import partial

from .state import State, WhateverState
from .event import Event, RestoreEvent
from .error import InvalidEventState


def validate_event_states(original_class, event):
    for state_name in event.from_states + (event.to_state,):
        state = original_class._pysm_states.get(state_name)
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


def register_state_to_instance(instance, state):
    if inspect.isclass(instance):
        raise ValueError('cannot register state to non instance object, '
                         'call register_state_to_class instead')
    if not (inspect.isclass(state) and issubclass(state, State)):
        raise ValueError('state is not a valid State')
    if not getattr(instance, 'initiated_pysm', False):
        raise TypeError('instance object is not a valid pysm state machine')

    state_name = state.__name__
    if state_name in instance.__dict__:
        raise TypeError('instance already has state: %s' % state_name)
    if '_pysm_states' not in instance.__dict__:
        instance.__dict__['_pysm_states'] = instance._pysm_states.copy()
    instance.__dict__[state_name] = state
    instance._pysm_states[state_name] = state


def register_state_to_class(clz, state, force=False):
    if not inspect.isclass(clz):
        raise ValueError('cannot register state to non class object, '
                         'call register_state_to_instance instead')
    if not (inspect.isclass(state) and issubclass(state, State)):
        raise ValueError('state is not a valid State')
    if not getattr(clz, 'initiated_pysm', False):
        raise TypeError('clz object is not a valid pysm state machine')

    state_name = state.__name__
    if state_name in clz.__dict__ and not force:
        raise TypeError('class already has state: %s' % state_name)
    clz._pysm_states[state_name] = state
    # clz.__dict__ is not writable; just setattr to clz
    setattr(clz, state_name, state)


def register_event_to_instance(instance, name, event):
    if inspect.isclass(instance):
        raise ValueError('cannot register event to non instance object, '
                         'call register_event_to_class instead')
    if not isinstance(event, Event):
        raise ValueError('event is not a valid Event')
    if not getattr(instance, 'initiated_pysm', False):
        raise TypeError('instance object is not a valid pysm state machine')

    if name in instance.__dict__:
        raise TypeError('instance already has event: %s' % name)
    if '_pysm_events' not in instance.__dict__:
        instance.__dict__['_pysm_events'] = instance._pysm_events.copy()
    instance.__dict__[name] = event
    instance._pysm_events[name] = event


def register_event_to_class(clz, name, event, force=False):
    if not inspect.isclass(clz):
        raise ValueError('cannot register event to non class object, '
                         'call register_event_to_instance instead')
    if not isinstance(event, Event):
        raise ValueError('event is not a valid Event')
    if not getattr(clz, 'initiated_pysm', False):
        raise TypeError('clz object is not a valid pysm state machine')

    if name in clz.__dict__ and not force:
        raise TypeError('class already has event: %s' % name)
    clz._pysm_events[name] = event
    # clz.__dict__ is not writable; just setattr to clz
    setattr(clz, name, event)


def state_machine(original_class):
    original_class.initiated_pysm = True
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
        validate_event_states(original_class, value)
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
