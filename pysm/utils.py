from .error import InvalidState
from .error import NoState
from .error import AlreadyHasState
from .error import AlreadyHasInitialState


def _nop(state, event):
    return True


def on_event(name):
    def wrapper(func):
        func.on_event = name
        return func
    return wrapper


def validate_add_state(obj, state_name, state, force):
    from .core import State
    if not isinstance(state, State):
        raise InvalidState('`%r` is not a valid State' % state)
    if obj.has_state(state_name) and not force:
        raise AlreadyHasState('`%s` already has state: %s' % (obj, state_name))


def validate_transition(obj, from_state, to_state, event):
    if not obj.has_state(from_state):
        raise NoState('unknown from state "{0}"'.format(from_state))
    if not obj.has_state(to_state):
        raise NoState('unknown to state "{0}"'.format(to_state))


def validate_initial_state(obj, state_name, force):
    if not obj.has_state(state_name):
        raise NoState('unknown initial state: {}'.format(state_name))
    if obj.initial is not None and not force:
        raise AlreadyHasInitialState(
            'multiple initial states, now: {}'.format(obj.initial)
        )
