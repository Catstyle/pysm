'''Python State Machine

Inspired by https://github.com/pgularski/pysm

The goal of this library is to give you a close to the State Pattern
simplicity with much more flexibility. And, if needed, the full state machine
functionality, including `FSM
<https://en.wikipedia.org/wiki/Finite-state_machine>`_, `HSM
<https://en.wikipedia.org/wiki/UML_state_machine
#Hierarchically_nested_states>`_, `PDA
<https://en.wikipedia.org/wiki/Pushdown_automaton>`_ and other tasty things.

Goals:
    - Provide a State Pattern-like behavior with more flexibility
    - Be explicit and don't add any code to objects
    - Handle directly any kind of event (not only strings) - parsing strings is
      cool again!
    - Keep it simple, even for someone who's not very familiar with the FSM
      terminology

----

.. |StateMachine| replace:: :class:`~.StateMachine`
.. |State| replace:: :class:`~.State`
.. |Hashable| replace:: :class:`~collections.Hashable`
.. |Iterable| replace:: :class:`~collections.Iterable`
.. |Callable| replace:: :class:`~collections.Callable`

'''
from collections import deque, defaultdict, Iterable
from itertools import product


def on_event(name):
    def wrapper(func):
        func.on_event = name
        return func
    return wrapper


class Event(object):

    def __init__(self, name, input=None, propagate=True, **cargo):
        self.name = name
        self.input = input
        self.cargo = cargo
        self.propagate = propagate

    def __repr__(self):
        return '<Event {}, input={}, cargo={}>'.format(
            self.name, self.input, self.cargo,
        )


class PysmError(Exception):
    '''All |StateMachine| exceptions are of this type. '''
    pass


class State(object):

    def __init__(self, name):
        self.name = name
        self.parent = None
        self.states = {}
        self.handlers = {}

    def _on(self, event):
        if event.name in self.handlers:
            event.propagate = False
            self.handlers[event.name](self, event)
        # Never propagate exit/enter events, even if propagate is set to True
        if (self.parent and event.propagate and
                event.name not in ['exit', 'enter']):
            self.parent._on(event)

    def _nop(self, event):
        del event  # Unused (silence pylint)
        return True

    def has_state(self, state):
        machines = deque()
        machines.append(self)
        while machines:
            machine = machines.popleft()
            if state in machine.states.values():
                return True
            for child_state in machine.states.values():
                if isinstance(child_state, StateMachine):
                    machines.append(child_state)
        return False

    @on_event('enter')
    def on_enter(self, event):
        pass

    @on_event('exit')
    def on_exit(self, event):
        pass


class StateMachine(State):

    STACK_SIZE = 32

    def __init__(self, name):
        super(StateMachine, self).__init__(name)
        self.state = None
        self.initial_state = None

        self.transitions = defaultdict(list)
        self.state_stack = deque(maxlen=self.STACK_SIZE)
        self.leaf_state_stack = deque(maxlen=self.STACK_SIZE)
        self.stack = deque()
        self.error_template = '{}'

    def _raise(self, ex):
        raise PysmError(self.error_template.format(ex))

    def _validate_transition(self, from_state, to_state, events, input):
        if from_state.name not in self.states:
            self._raise('unknown from state "{0}"'.format(from_state.name))
        root_machine = self.root_machine
        if (to_state and
                to_state is not root_machine and
                not root_machine.has_state(to_state)):
            self._raise('unknown to state "{0}"'.format(to_state.name))
        if not isinstance(events, Iterable):
            self._raise('events is not iterable: "{0}"'.format(events))
        if not isinstance(input, Iterable):
            self._raise('input is not iterable: "{0}"'.format(input))

    def _get_transition(self, event):
        leaf_state = self.leaf_state
        machine = leaf_state.parent
        key = (self.state, event.name, event.input)
        while machine:
            for transition in machine.transitions[key]:
                if transition['condition'](event) is True:
                    return transition
            machine = machine.parent
        return None

    def _get_leaf_state(self, state):
        while hasattr(state, 'state') and state.state is not None:
            state = state.state
        return state

    def _exit_states(self, event, from_state, to_state):
        if to_state is None:
            return
        state = self.leaf_state
        self.leaf_state_stack.append(state)
        while (state.parent and
                not (state.has_state(from_state) and
                     state.has_state(to_state)) or
                (state == from_state == to_state)):
            exit_event = Event('exit', propagate=False, source_event=event)
            exit_event.state_machine = self
            state._on(exit_event)
            state.parent.state_stack.append(state)
            state.parent.state = state.parent.initial_state
            state = state.parent
        return state

    def _enter_states(self, event, top_state, to_state):
        if to_state is None:
            return
        path = []
        state = self._get_leaf_state(to_state)

        while state.parent and state != top_state:
            path.append(state)
            state = state.parent
        for state in reversed(path):
            enter_event = Event('enter', propagate=False, source_event=event)
            enter_event.state_machine = self
            state._on(enter_event)
            state.parent.state = state

    @property
    def leaf_state(self):
        '''Get the current leaf state.

        The :attr:`~.StateMachine.state` property gives the current,
        local state in a state machine. The `leaf_state` goes to the bottom in
        a hierarchy of states. In most cases, this is the property that should
        be used to get the current state in a state machine, even in a flat
        FSM, to keep the consistency in the code and to avoid confusion.

        :returns: Leaf state in a hierarchical state machine
        :rtype: |State|

        '''
        return self._get_leaf_state(self)

    @property
    def root_machine(self):
        '''Get the root state machine in a states hierarchy.

        :returns: Root state in the states hierarchy
        :rtype: |StateMachine|

        '''
        machine = self
        while machine.parent:
            machine = machine.parent
        return machine

    def add_state(self, state_name, state, force=False):
        if not isinstance(state, State):
            raise TypeError('`%r` is not a valid State' % state)
        if state_name in self.states and not force:
            raise ValueError('`%s` already has state: %s' % (self, state_name))
        state.parent = self
        self.states[state_name] = state
        setattr(self, state_name, state)

    def add_states(self, states, force=False):
        for state in states:
            self.add_state(state.name, state, force)

    def set_initial_state(self, state):
        if state not in self.states.values():
            self._raise('unknown initial state')
        if self.initial_state is not None:
            self._raise('multiple initial states!')
        self.initial_state = state

    def add_transition(self, from_state, to_state, events, inputs=None,
                       action=None, condition=None, before=None, after=None):
        '''Add a transition to a state machine.

        All callbacks take two arguments - `state` and `event`. See parameters
        description for details.

        It is possible to create conditional if/elif/else-like logic for
        transitions. To do so, add many same transition rules with different
        condition callbacks. First met condition will trigger a transition, if
        no condition is met, no transition is performed.

        :param from_state: Source state
        :type from_state: |State|

        :param to_state: Target state. If `None`, then it's an `internal
            transition <https://en.wikipedia.org/wiki/UML_state_machine
            #Internal_transitions>`_
        :type to_state: |State|, `None`

        :param events: List of events that trigger the transition
        :type events: |Iterable| of |Hashable|

        :param inputs: List of inputs that trigger the transition. A transition
            event may be associated with a specific input. i.e.: An event may
            be ``parse`` and an input associated with it may be ``$``. May be
            `None` (default), then every matched event name triggers a
            transition.
        :type inputs: `None`, |Iterable| of |Hashable|

        :param action: Action callback that is called during the transition
            after all states have been left but before the new one is entered.

            `action` callback takes two arguments:

                - state: Leaf state before transition
                - event: Event that triggered the transition
        :type action: |Callable|

        :param condition: Condition callback - if returns `True` transition may
            be initiated.

            `condition` callback takes two arguments:

                - state: Leaf state before transition
                - event: Event that triggered the transition
        :type condition: |Callable|

        :param before: Action callback that is called right before the
            transition.

            `before` callback takes two arguments:

                - state: Leaf state before transition
                - event: Event that triggered the transition
        :type before: |Callable|

        :param after: Action callback that is called just after the transition

            `after` callback takes two arguments:

                - state: Leaf state after transition
                - event: Event that triggered the transition
        :type after: |Callable|

        '''
        # Rather than adding some if statements later on, let's just declare a
        # neutral items that will do nothing if called. It simplifies the logic
        # a lot.
        if inputs is None:
            inputs = [None]
        if action is None:
            action = self._nop
        if before is None:
            before = self._nop
        if after is None:
            after = self._nop
        if condition is None:
            condition = self._nop

        self._validate_transition(from_state, to_state, events, inputs)

        for event, input_value in product(events, inputs):
            self.transitions[(from_state, event, input_value)].append({
                'from_state': from_state,
                'to_state': to_state,
                'action': action,
                'condition': condition,
                'before': before,
                'after': after,
            })

    def add_transitions(self, transitions):
        self.transitions.update(transitions)

    def initialize(self):
        '''Initialize states in the state machine.

        After a state machine has been created and all states are added to it,
        :func:`initialize` has to be called.

        If using nested state machines (HSM),
        :func:`initialize` has to be called on a root
        state machine in the hierarchy.

        '''
        machines = deque()
        machines.append(self)
        while machines:
            machine = machines.popleft()
            # machine._enter_states(Event('enter'), machine.initial_state)
            machine.state = machine.initial_state
            for child_state in machine.states.values():
                if isinstance(child_state, StateMachine):
                    machines.append(child_state)

    def dispatch(self, event):
        '''Dispatch an event to a state machine.

        If using nested state machines (HSM), it has to be called on a root
        state machine in the hierarchy.

        :param event: Event to be dispatched
        :type event: :class:`.Event`

        '''
        event.state_machine = self
        leaf_state = self.leaf_state
        leaf_state._on(event)
        transition = self._get_transition(event)
        if transition is None:
            return
        to_state = transition['to_state']
        from_state = transition['from_state']

        transition['before'](event)
        top_state = self._exit_states(event, from_state, to_state)
        transition['action'](event)
        self._enter_states(event, top_state, to_state)
        transition['after'](event)

    def set_previous_leaf_state(self, event=None):
        '''Transition to a previous leaf state. This makes a dynamic transition
        to a historical state. The current `leaf_state` is saved on the stack
        of historical leaf states when calling this method.

        :param event: (Optional) event that is passed to states involved in the
            transition
        :type event: :class:`.Event`

        '''
        if event is not None:
            event.state_machine = self
        from_state = self.leaf_state
        try:
            to_state = self.leaf_state_stack.peek()
        except IndexError:
            return
        top_state = self._exit_states(event, from_state, to_state)
        self._enter_states(event, top_state, to_state)

    def revert_to_previous_leaf_state(self, event=None):
        '''Similar to :func:`set_previous_leaf_state`
        but the current leaf_state is not saved on the stack of states. It
        allows to perform transitions further in the history of states.

        '''
        self.set_previous_leaf_state(event)
        try:
            self.leaf_state_stack.pop()
        except IndexError:
            return


def state_machine(name):

    def wrapper(cls):
        cls.initiated_pysm = True
        cls.state_machine = StateMachine(name)

        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            cls_machine = cls.state_machine
            machine = self.state_machine = StateMachine(cls_machine.name)
            machine.states.update(cls_machine.states)
            machine.add_transitions(cls_machine.transitions)
            machine.set_initial_state(cls_machine.initial_state)
            machine.initialize()
            original_init(self, *args, **kwargs)
        cls.__init__ = new_init
        return cls
    return wrapper
