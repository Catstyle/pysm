import six
from pysm.errors import InvalidStateTransition


try:
    string_type = basestring
except NameError:
    string_type = str


class StateMeta(type):

    def __eq__(self, other):
        return other is WhateverState or self is other

    def __ne__(self, other):
        return not self == other

    def __unicode__(self):
        return self.name
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

    name = 'WhateverState'

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
        from_state.exit_state(instance, to_state)
        instance.__class__ = instance.current_state = to_state
        instance._adaptor.update(instance, to_state.name)
        to_state.enter_state(instance, from_state)


class RestoreEvent(Event):

    def __call__(self):
        restore_event = getattr(self.instance, 'restore_from_' + self.name)
        restore_event.to_state = self.instance.current_state
        return super(RestoreEvent, self).__call__()
