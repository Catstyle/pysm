from collections import defaultdict
from functools import partial
from six import string_types

from .error import InvalidTransition
from .error import NoState
from .error import InvalidState
from .error import AlreadyHasState
from .error import AlreadyHasInitialState
from .utils import get_event_handlers


class Event(object):

    def __init__(self, name, instance=None, input=None, propagate=True,
                 **cargo):
        self.name = name
        self.instance = instance
        self.input = input
        self.propagate = propagate
        self.cargo = cargo

    def __repr__(self):
        return '<Event {}, input={!r}, cargo={}>'.format(
            self.name, self.input, self.cargo,
        )


class State(object):

    def __init__(self, name, on_enter=None, on_exit=None):
        self.name = name
        self.handlers = get_event_handlers(self)
        self.on_enter = on_enter or self.on_enter
        self.on_exit = on_exit or self.on_exit

    def _on(self, event):
        if event.name in self.handlers:
            self.handlers[event.name](self, event)

    def on_enter(self, state, event):
        pass

    def on_exit(self, state, event):
        pass

    def __repr__(self):
        return '<State {}, handlers={}>'.format(
            self.name, self.handlers.keys()
        )


class Machine(object):

    StateClass = State

    def __init__(self, name):
        self.name = name
        self.initial = None
        self.states = {}
        self.transitions = defaultdict(list)
        self.wildcard_transitions = defaultdict(list)

    def _create_state(self, name, *args, **kwargs):
        return self.StateClass(name, *args, **kwargs)

    def _get_transition(self, state, event):
        instance = event.instance
        key = (state.name, event.name)
        transitions = instance.transitions[key] + self.transitions[key]
        if not transitions:
            raise InvalidTransition('{} cannot handle event {}'.format(
                state, event
            ))
        for transition in transitions:
            for cond, target in transition['conditions']:
                if isinstance(cond, list):
                    predicate = instance
                    for pre in cond:
                        predicate = getattr(predicate, pre)
                else:
                    predicate = cond
                if callable(predicate):
                    predicate = predicate(state, event)
                if predicate != target:
                    break
            else:
                return transition
        return None

    def _enter_state(self, state, from_state, event):
        event.instance.state = state.name
        state.on_enter(from_state, event)

    def _exit_state(self, state, to_state, event):
        state.on_exit(to_state, event)
        event.instance.state = None

    def _switch_state(self, instance, to_state, event=None):
        event = event or Event('switch', instance)
        from_state = self.states[instance.state]
        self._exit_state(from_state, to_state, event)
        to_state = self.states[to_state]
        self._enter_state(to_state, from_state, event)

    def _init_instance(self, instance):
        '''Initialize states in the state machine.

        After a state machine has been created and all states are added to it,
        :func:`initialize` has to be called when creating instance of host.

        Note: should not called from outside, this method would reset instance
        attributes
        '''
        instance.states = {}
        instance.transitions = defaultdict(list)

        state = self.get_state(self.initial)
        instance.state = state.name
        state.on_enter(None, Event('initialize'))
        setattr(instance, 'dispatch', partial(self.dispatch, instance))

    def _reset(self):
        self.initial = None
        self.states = {}
        self.transitions = defaultdict(list)

    def _validate_add_state(self, state_name, state, force):
        if not isinstance(state, State):
            raise InvalidState('`%r` is not a valid State' % state)
        if self.has_state(state_name) and not force:
            raise AlreadyHasState(
                '`%s` already has state: %s' % (self, state_name)
            )

    def _validate_transition(self, from_state, to_state, event):
        if not self.has_state(from_state) and from_state != '*':
            raise NoState('unknown from state "{0}"'.format(from_state))
        if not self.has_state(to_state):
            raise NoState('unknown to state "{0}"'.format(to_state))

    def _validate_initial_state(self, state_name, force):
        if not self.has_state(state_name):
            raise NoState('unknown initial state: {}'.format(state_name))
        if self.initial is not None and not force:
            raise AlreadyHasInitialState(
                'multiple initial states, now: {}'.format(self.initial)
            )

    def _prepare_transition(self, from_state, to_state, event,
                            conditions=None, before=None, after=None):
        _conditions = []
        if conditions is not None:
            if not isinstance(conditions, list):
                conditions = [conditions]
        else:
            conditions = []
        for cond in conditions:
            if isinstance(cond, string_types):
                if cond.startswith('!'):
                    predicate, target = cond[1:].split('.'), False
                else:
                    predicate, target = cond.split('.'), True
            else:
                predicate, target = cond, True
            _conditions.append((predicate, target))
        return {
            'from_state': from_state,
            'to_state': to_state,
            'conditions': _conditions,
            'before': before,
            'after': after,
        }

    def add_state(self, name, state=None, force=False):
        state = state or self._create_state(name)
        self._validate_add_state(name, state, force)
        self.states[name] = state

    def add_states(self, states, initial=None, force=False):
        for state in states:
            if isinstance(state, string_types):
                self.add_state(state, force=force)
            elif isinstance(state, dict):
                state = self._create_state(**state)
                self.add_state(state.name, state, force=force)
            elif isinstance(state, State):
                self.add_state(state.name, state, force=force)
        if initial:
            self.set_initial_state(initial, force=force)

    def has_state(self, state_name):
        return state_name in self.states

    def get_state(self, state_name):
        if state_name not in self.states:
            raise NoState('{} has no such state {}'.format(self, state_name))
        return self.states[state_name]

    def set_initial_state(self, state_name, force=False):
        self._validate_initial_state(state_name, force)
        self.initial = state_name

    def add_transition(self, from_state, to_state, event,
                       conditions=None, before=None, after=None):
        '''Add a transition to a state machine.

        All callbacks take two arguments - `state` and `event`. See parameters
        description for details.

        It is possible to create conditional if/elif/else-like logic for
        transitions. To do so, add many same transition rules with different
        condition callbacks. First met condition will trigger a transition, if
        no condition is met, no transition is performed.

        :param from_state: Source state
        :type from_state: |string|

        :param to_state: Target state.
            If it is `from_state`, then it's an `internal transition
            <https://en.wikipedia.org/wiki/UML_state_machine
             #Internal_transitions>`_
        :type to_state: |string|

        :param event: event that trigger the transition
        :type event: |string|

        :param conditions: Condition callback - if all returns `True`
            transition may be initiated.

            `condition` callback takes two arguments:

                - state: State before transition
                - event: Event that triggered the transition
        :type conditions: |Iterable| of |Callable|

        :param before: Action callback that is called right before the
            transition.

            `before` callback takes two arguments:

                - state: State before transition
                - event: Event that triggered the transition
        :type before: |Callable|

        :param after: Action callback that is called just after the transition

            `after` callback takes two arguments:

                - state: State after transition
                - event: Event that triggered the transition
        :type after: |Callable|

        '''
        self._validate_transition(from_state, to_state, event)
        transition = self._prepare_transition(
            from_state, to_state, event, conditions, before, after
        )
        if from_state == '*':
            self.wildcard_transitions[event].append(transition)
        else:
            self.transitions[(from_state, event)].append(transition)
        for event, transitions in self.wildcard_transitions.items():
            for from_state in self.states:
                self.transitions[(from_state, event)].extend(transitions)

    def add_transitions(self, transitions):
        for transition in transitions:
            if isinstance(transition, list):
                self.add_transition(*transition)
            elif isinstance(transition, dict):
                self.add_transition(**transition)

    def reinit_instance(self, instance):
        state = self.get_state(self.initial)
        instance.state = state.name
        state.on_enter(None, Event('reinit', instance))

    def dispatch(self, instance, event):
        '''Dispatch an event to a state machine.

        If using nested state machines (HSM), it has to be called on a root
        state machine in the hierarchy.

        :param event: Event to be dispatched
        :type event: :class:`.Event`

        '''
        get_state = self.get_state
        state_name = instance.state
        state = instance.states.get(state_name) or get_state(state_name)
        event.instance = instance
        state._on(event)
        transition = self._get_transition(state, event)
        if transition is None:
            return
        to_state = transition['to_state']
        to_state = instance.states.get(to_state) or get_state(to_state)

        before = transition['before']
        if isinstance(before, string_types):
            before = getattr(instance, before)
        if before:
            before(state, event)
        self._exit_state(state, to_state, event)
        self._enter_state(to_state, state, event)
        after = transition['after']
        if isinstance(after, string_types):
            after = getattr(instance, after)
        if after:
            after(to_state, event)

    def __repr__(self):
        return '<Machine: {}, states: {}>'.format(
            self.name, self.states.keys()
        )


def state_machine(name, machine_class=None):

    def wrapper(cls):
        cls.initiated_pysm = True
        cls.machine = (machine_class or Machine)(name)

        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            cls.machine._init_instance(self)
            original_init(self, *args, **kwargs)
        cls.__init__ = new_init
        return cls
    return wrapper
