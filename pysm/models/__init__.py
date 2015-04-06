try:
    string_type = basestring
except NameError:
    string_type = str
import inspect

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


class State(object):

    __metaclass__ = StateMeta

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

    @staticmethod
    def enter_state(self, from_state):
        pass

    @staticmethod
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
        from_state.exit_state(instance, to_state)
        for name, method in instance._origin_methods.items():
            instance.__dict__[name] = method
        instance._origin_methods.clear()
        for name, method in to_state.__dict__.items():
            if not name.startswith('_') and inspect.ismethod(method):
                if name in instance.__dict__:
                    instance._origin_methods[name] = getattr(instance, name)
                instance.__dict__[name] = method
        instance.current_state = to_state
        instance._adaptor.update(instance, to_state.__name__)
        to_state.enter_state(instance, from_state)


class RestoreEvent(Event):

    def __call__(self):
        restore_event = getattr(self.instance, 'restore_from_' + self.name)
        restore_event.to_state = self.instance.current_state
        return super(RestoreEvent, self).__call__()
