import six
from inspect import isfunction
from functools import partial

from pysm.errors import InvalidStateTransition


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
        if isinstance(other, six.string_type):
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
        self.from_states = from_states
        self.to_state = to_state

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
        def switch(*args, **kwargs):
            current_state = instance.current_state
            if current_state not in self.from_states:
                raise InvalidStateTransition(
                    '%s: calling `%s` from state `%s`, valid states `%s`' % (
                        instance, self.name, current_state, self.from_states
                    )
                )
            switch_state(instance, current_state, self.to_state, *args, **kwargs)
        return switch

    def __str__(self):
        return u'pysm-event|%s' % self.name
    __unicode__ = __repr__ = __str__


class RestoreEvent(Event):

    def __get__(self):
        restore_event = getattr(self.instance, 'restore_from_' + self.name)
        restore_event.to_state = self.instance.current_state
        return super(RestoreEvent, self).__get__()

    def __str__(self):
        return u'pysm-restoreevent|%s' % self.name
    __unicode__ = __repr__ = __str__


def attach_state(instance, state):
    base_dict = instance.__class__.__dict__
    for name, method in state.__dict__.items():
        if not name.startswith('_') and isfunction(method):
            if name in base_dict:
                instance._pysm_origin_methods[name] = base_dict[name]
            setattr(instance, name, partial(method, instance))
            instance._pysm_state_methods.add(name)
    instance.current_state = state
    instance._adaptor.update(instance, state.__name__)


def detach_state(instance):
    state = instance.current_state
    for name in instance._pysm_state_methods:
        delattr(instance, name)
    instance._pysm_state_methods.clear()
    for name, method in instance._pysm_origin_methods.items():
        setattr(instance, name, partial(method, instance))
    instance._pysm_origin_methods.clear()
    instance.current_state = None
    return state

def switch_state(instance, from_state, to_state, *args, **kwargs):
    instance.exit_state(to_state)
    detach_state(instance)
    attach_state(instance, to_state)
    instance.enter_state(from_state, *args, **kwargs)
