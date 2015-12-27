import inspect
from six import add_metaclass, string_types

from .event import Event, RestoreEvent, attach_state


class StateMeta(type):

    def __new__(cls, name, bases, attrs):
        cls = type.__new__(cls, name, bases, attrs)
        cls.state_methods = {}
        for base in bases:
            for name, value in base.__dict__.items():
                if not name.startswith('_') and inspect.isfunction(value):
                    cls.state_methods[name] = value
        for name, value in attrs.items():
            if not name.startswith('_') and inspect.isfunction(value):
                cls.state_methods[name] = value
        return cls

    def __eq__(self, other):
        return self is other or self is WhateverState or other is WhateverState

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return id(self.__name__)

    def __unicode__(self):
        return self.__name__
    __str__ = __unicode__


@add_metaclass(StateMeta)
class State(object):

    def enter_state(self, from_state):
        pass

    def exit_state(self, to_state):
        pass

    def __eq__(self, other):
        if isinstance(other, string_types):
            return self.__class__.__name__ == other
        elif isinstance(other, State):
            return self.__class__ == other.__class__
        else:
            return NotImplemented

    def __ne__(self, other):
        return not self == other


class WhateverState(State):
    pass


def state_machine(original_class):
    initial_state = process_states(original_class)
    process_events(original_class)

    original_init = original_class.__init__
    def new_init(self, *args, **kwargs):
        self._pysm_origin_methods = {}
        self._pysm_state_methods = set()
        attach_state(self, initial_state)
        original_init(self, *args, **kwargs)
    original_class.__init__ = new_init
    return original_class


def process_states(original_class):
    initial_state = None
    original_class._pysm_states = {}
    for name, value in inspect.getmembers(original_class):
        if not (inspect.isclass(value) and issubclass(value, State)):
            continue
        if issubclass(value, WhateverState):
            raise TypeError('cannot inherit from WhateverState')

        original_class._pysm_states[name] = value
        if getattr(value, 'initial', False):
            if initial_state is not None:
                raise ValueError("multiple initial states!")
            initial_state = original_class._pysm_initial_state = value

    assert initial_state, 'missing initial state'
    return initial_state


def process_events(original_class):
    for name, value in inspect.getmembers(original_class):
        if not isinstance(value, Event):
            continue
        value.name = name

        if isinstance(value, RestoreEvent):
            restore_name = 'restore_from_' + name
            restore_event = Event(
                from_states=value.to_state, to_state=WhateverState
            )
            restore_event.name = restore_name
            setattr(original_class, restore_name, restore_event)
