try:
    string_type = basestring
except NameError:
    string_type = str

from pysm.errors import InvalidStateTransition


class State(object):

    def enter_state(self, from_state):
        raise NotImplementedError

    def exit_state(self, to_state):
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, string_type):
            return self.__class__ == other.__class__
        elif isinstance(other, State):
            return self.__class__ == other.__class__
        else:
            return False

    def __ne__(self, other):
        return not self == other


class Event(object):

    def __init__(self, from_states, to_state):
        assert from_states
        assert to_state
        self.to_state = to_state
        if isinstance(from_states, (tuple, list)):
            self.from_states = tuple(from_states)
        else:
            self.from_states = (from_states,)

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


class Whatever(State):

    name = 'Whatever'

    def enter_state(self, from_state):
        pass

    def exit_state(self, to_state):
        pass
