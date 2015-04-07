import six
from pysm.errors import InvalidStateTransition


try:
    string_type = basestring
except NameError:
    string_type = str
from inspect import isfunction
from functools import partial


class StateMeta(type):

    def __eq__(self, other):
        return other is WhateverState or self is other

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return id(self.__name__)

    def __unicode__(self):
        return self.__name__
    __str__ = __unicode__


@six.add_metaclass(StateMeta)
class State(object):

    def enter_state(self, from_state):
        raise NotImplementedError

    def exit_state(self, to_state):
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, string_type):
            return self.__class__.__name__ == other
        elif isinstance(other, State):
            return self.__class__ == other.__class__
        else:
            return False

    def __ne__(self, other):
        return not self == other


class WhateverState(State):

    def enter_state(self, from_state):
        pass

    def exit_state(self, to_state):
        pass


class Event(object):

    def __init__(self, from_states, to_state):
        assert from_states
        assert to_state
        self.to_state = to_state
        self.from_states = from_states

    @property
    def from_states(self):
        return self._from_states
    
    @from_states.setter
    def from_states(self, from_states):
        if isinstance(from_states, (tuple, list)):
            self._from_states = tuple(from_states)
        else:
            self._from_states = (from_states,)

    def __get__(self, instance, owner):
        self.instance, self.owner = instance, owner
        return self

    def __call__(self):
        #assert current state
        instance = self.instance
        current_state = self.instance.current_state
        if current_state not in self.from_states:
            raise InvalidStateTransition(
                'calling `%s` from state `%s`, valid states `%s`' % (
                    self.name, current_state, self.from_states
                )
            )
        self.__switch__(instance, current_state, self.to_state)

    def __switch__(self, instance, from_state, to_state):
        instance.exit_state(to_state)
        detach_state(instance)
        attach_state(instance, to_state)
        instance.enter_state(from_state)


class RestoreEvent(Event):

    def __call__(self):
        restore_event = getattr(self.instance, 'restore_from_' + self.name)
        restore_event.to_state = self.instance.current_state
        return super(RestoreEvent, self).__call__()


def attach_state(instance, state):
    original_class = instance.__class__
    for name, method in state.__dict__.items():
        if not name.startswith('_') and isfunction(method):
            if name in original_class.__dict__:
                original_class._origin_methods[name] = original_class.__dict__[name]
            setattr(original_class, name, partial(method, instance))
            original_class._state_methods.add(name)
    instance.current_state = state
    instance._adaptor.update(instance, state.__name__)


def detach_state(instance):
    original_class, state = instance.__class__, instance.current_state
    for name in original_class._state_methods:
        delattr(original_class, name)
    original_class._state_methods.clear()
    for name, method in original_class._origin_methods.items():
        setattr(original_class, name, method)
    original_class._origin_methods.clear()
    instance.current_state = None
    return state
