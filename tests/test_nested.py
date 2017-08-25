# -*- coding: utf-8 -*-
# import sys
from unittest import TestCase
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from pysm.core import Event, state_machine
from pysm.nested import NestedState, NestedMachine
from pysm.error import AlreadyHasInitialState

state_separator = NestedState.separator


@state_machine('test', NestedMachine)
class Stuff(object):
    pass


class TestTransitions(TestCase):

    def setUp(self):
        Stuff.machine._reset()

    def tearDown(self):
        NestedState.separator = state_separator

    def test_initial(self):
        # Define with list of dictionaries
        states = ['A', 'B', {'name': 'C', 'children': ['1', '2', '3']}, 'D']
        m = Stuff.machine
        m.add_states(states, 'A', force=True)

        self.assertIsNotNone(m.initial)
        self.assertEqual(m.initial, 'A')

        with self.assertRaises(AlreadyHasInitialState):
            m.set_initial_state('C')
        m.set_initial_state('C', force=True)
        self.assertEqual(m.initial, 'C')

    def test_dispatch(self):
        states = [NestedState('State1'), 'State2', {'name': 'State3'}]
        transitions = [
            {
                'event': 'advance',
                'from_state': 'State2',
                'to_state': 'State3'
            }
        ]
        m = Stuff.machine
        m.add_states(states)
        m.add_transitions(transitions)
        m.set_initial_state('State2')
        s = Stuff()
        s.dispatch(Event('advance'))
        self.assertEqual(s.state, 'State3')

    def test_transition_definitions(self):
        states = ['A', 'B', {'name': 'C', 'children': ['1', '2', '3']}, 'D']
        # Define with list of dictionaries
        transitions = [
            {'event': 'walk', 'from_state': 'A', 'to_state': 'B'},
            {'event': 'run', 'from_state': 'B', 'to_state': 'C'},
            {'event': 'sprint', 'from_state': 'C', 'to_state': 'D'},
            {'event': 'run', 'from_state': 'C', 'to_state': 'C.1'},
        ]
        m = Stuff.machine
        m.add_states(states, initial='A', force=True)
        m.add_transitions(transitions)

        s = Stuff()
        s.dispatch(Event('walk'))
        self.assertEqual(s.state, 'B')
        s.dispatch(Event('run'))
        self.assertEqual(s.state, 'C')
        s.dispatch(Event('run'))
        self.assertEqual(s.state, 'C.1')

        # Define with list of lists
        transitions = [
            ['A', 'B', 'walk'],
            ['B', 'C', 'run'],
            ['C', 'D', 'sprint']
        ]
        m._reset()
        m.add_states(states, initial='A')
        m.add_transitions(transitions)

        s = Stuff()
        s.dispatch(Event('walk'))
        s.dispatch(Event('run'))
        s.dispatch(Event('sprint'))
        self.assertEqual(s.state, 'D')

    # def test_multiple_add_transitions_from_state(self):
    #     s = self.stuff
    #     s.machine.add_transition(
    #         'advance', 'A', 'B', conditions=['this_fails'])
    #     s.machine.add_transition('advance', 'A', 'C')
    #     s.machine.add_transition('advance', 'C', 'C%s2' % State.separator)
    #     s.advance()
    #     self.assertEqual(s.state, 'C')
    #     s.advance()
    #     self.assertEqual(s.state, 'C%s2' % State.separator)
    #     self.assertFalse(s.is_C())
    #     self.assertTrue(s.is_C(allow_substates=True))

    # def test_add_custom_state(self):
    #     s = self.stuff
    #     s.machine.add_states([{'name': 'E', 'children': ['1', '2', '3']}])
    #     s.machine.add_transition('go', '*', 'E%s1' % State.separator)
    #     s.machine.add_transition('run', 'E', 'C.3.a')
    #     s.go()
    #     s.run()

    def test_enter_exit_nested_state(self):
        mock = MagicMock()

        def callback():
            mock()
        states = [
            'A', 'B',
            {'name': 'C', 'on_enter': callback, 'on_exit': callback,
             'children': [{'name': '1', 'on_exit': callback}, '2', '3']},
            'D'
        ]
        transitions = [['A', 'C.1', 'go'], ['C', 'D', 'go']]

        m = Stuff.machine
        m.add_states(states=states, initial='A')
        m.add_transitions(transitions)
        m.dispatch(Event('go'))
        self.assertTrue(mock.called)
        self.assertEqual(mock.call_count, 1)
        m.go()
        self.assertTrue(m.is_D())
        self.assertEqual(mock.call_count, 3)

    # def test_state_change_listeners(self):
    #     m = Stuff.machine
    #     m.add_transition('advance', 'A', 'C.1')
    #     m.add_transition('reverse', 'C', 'A')
    #     m.add_transition('lower', 'C.1', 'C.3.a')
    #     m.add_transition('rise', 'C.3', 'C.1')
    #     m.add_transition('fast', 'A', 'C.3.a'))
    #     m.on_enter_C('hello_world')
    #     m.on_exit_C('goodbye')
    #     m.on_enter('C{0}3{0}a'.format(State.separator), 'greet')
    #     m.on_exit('C%s3' % State.separator, 'meet')
    #     m.advance()
    #     self.assertEqual(s.state, 'C%s1' % State.separator)
    #     self.assertEqual(s.message, 'Hello World!')
    #     s.lower()
    #     self.assertEqual(s.state, 'C{0}3{0}a'.format(State.separator))
    #     self.assertEqual(s.message, 'Hi')
    #     s.rise()
    #     self.assertEqual(s.state, 'C%s1' % State.separator)
    #     self.assertTrue(s.message.startswith('Nice to'))
    #     s.reverse()
    #     self.assertEqual(s.state, 'A')
    #     self.assertTrue(s.message.startswith('So long'))
    #     s.fast()
    #     self.assertEqual(s.state, 'C{0}3{0}a'.format(State.separator))
    #     self.assertEqual(s.message, 'Hi')
    #     s.to_A()
    #     self.assertEqual(s.state, 'A')
    #     self.assertTrue(s.message.startswith('So long'))

    # def test_enter_exit_nested(self):
    #     m = Stuff.machine
    #     m.add_transition('advance', 'A', 'C.1')
    #     m.add_transition('reverse', 'C', 'A')
    #     m.add_transition('lower', 'C.1', 'C.3.a'))
    #     m.add_transition('rise', 'C.3', 'C.1')
    #     m.add_transition('fast', 'A', 'C.3.a')
    #     for name, state in s.machine.states.items():
    #         state.on_enter.append('increase_level')
    #         state.on_exit.append('decrease_level')

    #     s.advance()
    #     self.assertEqual(s.state, 'C%s1' % State.separator)
    #     self.assertEqual(s.level, 2)
    #     s.lower()
    #     self.assertEqual(s.state, 'C{0}3{0}a'.format(State.separator))
    #     self.assertEqual(s.level, 3)
    #     s.rise()
    #     self.assertEqual(s.state, 'C%s1' % State.separator)
    #     self.assertEqual(s.level, 2)
    #     s.reverse()
    #     self.assertEqual(s.state, 'A')
    #     self.assertEqual(s.level, 1)
    #     s.fast()
    #     self.assertEqual(s.state, 'C{0}3{0}a'.format(State.separator))
    #     self.assertEqual(s.level, 3)
    #     s.to_A()
    #     self.assertEqual(s.state, 'A')
    #     self.assertEqual(s.level, 1)
    #     if State.separator in '_':
    #         s.to_C_3_a()
    #     else:
    #         s.to_C.s3.a()
    #     self.assertEqual(s.state, 'C{0}3{0}a'.format(State.separator))
    #     self.assertEqual(s.level, 3)

    # def test_ordered_transitions(self):
    #     states = [
    #         {'name': 'first',
    #          'children': ['second', 'third', {
    #              'name': 'fourth', 'children': ['fifth', 'sixth']
    #          }, 'seventh']}, 'eighth', 'ninth']
    #     m = self.stuff.machine_cls(states=states)
    #     m.add_ordered_transitions()
    #     self.assertEqual(m.state, 'initial')
    #     m.next_state()
    #     self.assertEqual(m.state, 'first')
    #     m.next_state()
    #     m.next_state()
    #     self.assertEqual(m.state, 'first{0}third'.format(State.separator))
    #     m.next_state()
    #     m.next_state()
    #     self.assertEqual(m.state, 'first.fourth.fifth')
    #     m.next_state()
    #     m.next_state()
    #     self.assertEqual(m.state, 'first{0}seventh'.format(State.separator))
    #     m.next_state()
    #     m.next_state()
    #     self.assertEqual(m.state, 'ninth')

    #     # Include initial state in loop
    #     m = self.stuff.machine_cls('self', states)
    #     m.add_ordered_transitions(loop_includes_initial=False)
    #     m.to_ninth()
    #     m.next_state()
    #     self.assertEqual(m.state, 'first')

    #     # Test user-determined sequence and event name
    #     m = self.stuff.machine_cls('self', states, initial='first')
    #     m.add_ordered_transitions(['first', 'ninth'], event='advance')
    #     m.advance()
    #     self.assertEqual(m.state, 'ninth')
    #     m.advance()
    #     self.assertEqual(m.state, 'first')

    #     # Via init argument
    #     m = Stuff.machine
    #     m.next_state()
    #     self.assertEqual(m.state, 'first{0}second'.format(State.separator))

    # def test_callbacks_duplicate(self):

    #     transitions = [
    #         {'event': 'walk', 'from_state': 'A', 'to_state': 'C',
    #          'before': 'before_change', 'after': 'after_change'},
    #         {'event': 'run', 'from_state': 'B', 'to_state': 'C'}
    #     ]

    #     m = Stuff.machine(states=['A', 'B', 'C'], transitions=transitions,
    #                                before_state_change='before_change',
    #                                after_state_change='after_change',
    #                                initial='A', auto_transitions=True)

    #     m.before_change = MagicMock()
    #     m.after_change = MagicMock()

    #     m.walk()
    #     self.assertEqual(m.before_change.call_count, 2)
    #     self.assertEqual(m.after_change.call_count, 2)

    # def test_with_custom_separator(self):
    #     State.separator = '.'
    #     self.setUp()
    #     self.test_enter_exit_nested()
    #     self.setUp()
    #     self.test_state_change_listeners()
    #     self.test_nested_auto_transitions()
    #     State.separator = '.' if sys.version_info[0] < 3 else u'↦'
    #     self.setUp()
    #     self.test_enter_exit_nested()
    #     self.setUp()
    #     self.test_state_change_listeners()
    #     self.test_nested_auto_transitions()

    # def test_with_slash_separator(self):
    #     State.separator = '/'
    #     self.setUp()
    #     self.test_enter_exit_nested()
    #     self.setUp()
    #     self.test_state_change_listeners()
    #     self.test_nested_auto_transitions()
    #     self.setUp()
    #     self.test_ordered_transitions()

    # def test_nested_auto_transitions(self):
    #     s = self.stuff
    #     s.to_C()
    #     self.assertEqual(s.state, 'C')
    #     state = 'C{0}3{0}a'.format(State.separator)
    #     s.to(state)
    #     self.assertEqual(s.state, state)

    # def test_example_one(self):
    #     State.separator = '_'
    #     states = [
    #         'standing', 'walking',
    #         {'name': 'caffeinated', 'children': ['dithering', 'running']}
    #     ]
    #     transitions = [['walk', 'standing', 'walking'],
    #                    ['stop', 'walking', 'standing'],
    #                    ['drink', '*', 'caffeinated'],
    #                    ['walk', 'caffeinated', 'caffeinated_running'],
    #                    ['relax', 'caffeinated', 'standing']]
    #     m = Stuff.machine(states=states, initial='standing', name='Machine1')

    #     machine.walk()   # Walking now
    #     machine.stop()   # let's stop for a moment
    #     machine.drink()  # coffee time
    #     machine.state
    #     self.assertEqual(machine.state, 'caffeinated')
    #     machine.walk()   # we have to go faster
    #     self.assertEqual(machine.state, 'caffeinated_running')
    #     machine.stop()   # can't stop moving!
    #     machine.state
    #     self.assertEqual(machine.state, 'caffeinated_running')
    #     machine.relax()  # leave nested state
    #     machine.state    # phew, what a ride
    #     self.assertEqual(machine.state, 'standing')
    #     machine.to_caffeinated_running()  # auto transition fast track
    #     machine.on_enter_caffeinated_running('callback_method')

    # def test_get_triggers(self):
    #     states = [
    #         'standing', 'walking',
    #         {'name': 'caffeinated', 'children': ['dithering', 'running']}]
    #     transitions = [
    #         ['walk', 'standing', 'walking'],
    #         ['go', 'standing', 'walking'],
    #         ['stop', 'walking', 'standing'],
    #         {'event': 'drink', 'from_state': '*',
    #          'to_state': 'caffeinated_dithering',
    #          'conditions': 'is_hot', 'unless': 'is_too_hot'},
    #         ['walk', 'caffeinated_dithering', 'caffeinated_running'],
    #         ['relax', 'caffeinated', 'standing']
    #     ]

    #     m = Stuff.machine(states=states, transitions=transitions)
    #     trans = machine.get_triggers('caffeinated.dithering')
    #     self.assertEqual(len(trans), 3)
    #     self.assertTrue('relax' in trans)
