from collections import deque, defaultdict
from functools import partial
from six import string_types

from .core import Event, State, Machine
from .utils import validate_initial_state


class NestedState(State):

    separator = '.'

    def __init__(self, name, parent=None, initial=None):
        super(NestedState, self).__init__(name)
        self.parent = parent
        if parent:
            parent.children[self.name] = self
            self.name = parent.name + self.separator + self.name
        self.children = {}
        self.initial = initial

    def _on(self, event):
        if event.name in self.handlers:
            event.propagate = False
            self.handlers[event.name](self, event)
        # Never propagate exit/enter events, even if propagate is set to True
        if self.parent and event.propagate:
            self.parent._on(event)

    def set_initial_state(self, state_name):
        validate_initial_state(self, state_name)
        self.initial = state_name

    def __repr__(self):
        return '<NestedState {}, handlers={}>'.format(
            self.name, self.handlers.keys()
        )


class NestedMachine(Machine):

    StateClass = NestedState
    STACK_SIZE = 32

    def _get_top_state(self, state, other_state):
        ancestors = []
        other_ancestors = []
        while state.parent:
            ancestors.append(state.parent)
            state = state.parent
        while other_state.parent:
            other_ancestors.append(other_state.parent)
            other_state = other_state.parent

        top = None
        for ancestor, other_ancestor in zip(reversed(ancestors),
                                            reversed(other_ancestors)):
            if ancestor is other_ancestor:
                top = ancestor
            else:
                break
        return top

    def _enter_state(self, instance, state, from_state=None, event=None):
        instance.state = state.name
        top_state = event.cargo.get('top_state') or \
            self._get_top_state(state, from_state)
        path = [state]
        while state.parent and state.parent != top_state:
            path.append(state.parent)
            state = state.parent
        for state in reversed(path):
            state.enter_state(instance, from_state, event)

    def _exit_state(self, instance, state, to_state=None, event=None):
        instance.state_stack.append(state)
        state.exit_state(instance, to_state, event)
        top_state = self._get_top_state(state, to_state)
        while state.parent and state.parent != top_state:
            state.parent.exit_state(instance, to_state, event)
            state = state.parent
        instance.state = None
        event.cargo['top_state'] = top_state

    def _init_instance(self, instance):
        instance.states = {}
        instance.transitions = defaultdict(list)
        instance.state_stack = deque(maxlen=self.STACK_SIZE)

        state = self.get_state(self.initial)
        instance.state = state.name
        state.enter_state(instance, None, Event('initialize'))
        setattr(instance, 'dispatch', partial(self.dispatch, instance))

    def traverse(self, states, parent=None, remap={}):
        new_states = []
        for state in states:
            tmp_states = []
            # other state representations are handled almost like in the
            # base class but a parent parameter is added
            if isinstance(state, string_types):
                if state in remap:
                    continue
                tmp_states.append(self._create_state(state, parent=parent))
            elif isinstance(state, dict):
                if state['name'] in remap:
                    continue

                if 'children' in state:
                    # Concat the state names with the current scope.
                    # The scope is the concatenation of all # previous parents.
                    # Call traverse again to check for more nested states.
                    p = self._create_state(
                        state['name'], parent=parent,
                        initial=state.get('initial')
                    )
                    nested = self.traverse(
                        state['children'], parent=p,
                        remap=state.get('remap', {})
                    )
                    tmp_states.append(p)
                    tmp_states.extend(nested)
                else:
                    tmp_states.append(self._create_state(**state))
            elif isinstance(state, NestedState):
                tmp_states.append(state)
            else:
                raise ValueError(
                    "{} is not an instance of NestedState "
                    "required by NestedMachine.".format(state)
                )
            new_states.extend(tmp_states)

        duplicate_check = set()
        for s in new_states:
            name = s.name
            if name in duplicate_check:
                raise ValueError(
                    "State %s cannot be added since it is already in "
                    "state list %s.".format(name, [n.name for n in new_states])
                )
            duplicate_check.add(name)
        return new_states

    def add_states(self, states, initial=None, force=False):
        states = self.traverse(states)
        super(NestedMachine, self).add_states(states, initial, force)

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
            to_state = self.state_stack[-1]
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
            self.state_stack.pop()
        except IndexError:
            return
