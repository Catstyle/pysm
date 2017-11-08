# -*- coding: utf-8 -*-
from unittest import TestCase
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from pysm.core import Machine, State, Event, state_machine
from pysm.error import AlreadyHasInitialState, InvalidTransition


@state_machine('test', Machine)
class Stuff(object):
    pass


class TestCore(TestCase):

    def setUp(self):
        Stuff.machine._reset()

    def tearDown(self):
        pass

    def test_initial(self):
        # Define with list of dictionaries
        states = ['A', 'B', {'name': 'C'}, 'D']
        m = Stuff.machine
        m.add_states(states, 'A', force=True)

        self.assertIsNotNone(m.initial)
        self.assertEqual(m.initial, 'A')

        with self.assertRaises(AlreadyHasInitialState):
            m.set_initial_state('C')
        m.set_initial_state('C', force=True)
        self.assertEqual(m.initial, 'C')

    def test_dispatch(self):
        states = [State('State1'), 'State2', {'name': 'State3'}]
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
        states = ['A', 'B', {'name': 'C'}, 'D']
        # Define with list of dictionaries
        transitions = [
            {'event': 'walk', 'from_state': 'A', 'to_state': 'B'},
            {'event': 'run', 'from_state': 'B', 'to_state': 'C'},
            {'event': 'sprint', 'from_state': 'C', 'to_state': 'D'},
            {'event': 'run', 'from_state': 'C', 'to_state': 'A'},
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
        self.assertEqual(s.state, 'A')

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

    # def test_add_custom_state(self):
    #     s = self.stuff
    #     s.machine.add_states([{'name': 'E', 'children': ['1', '2', '3']}])
    #     s.machine.add_transition('go', '*', 'E%s1' % State.separator)
    #     s.machine.add_transition('run', 'E', 'C.3.a')
    #     s.go()
    #     s.run()

    def test_enter_exit_nested_state(self):
        mock = MagicMock()

        def callback(state, event):
            mock()
        states = [
            'A', 'B',
            {'name': 'C', 'on_enter': callback, 'on_exit': callback},
            'D'
        ]
        transitions = [['A', 'C', 'go'], ['C', 'D', 'go']]

        m = Stuff.machine
        m.add_states(states=states, initial='A')
        m.add_transitions(transitions)
        s = Stuff()
        s.dispatch(Event('go'))
        self.assertEqual(s.state, 'C')
        self.assertTrue(mock.called)
        self.assertEqual(mock.call_count, 1)
        s.dispatch(Event('go'))
        self.assertEqual(s.state, 'D')
        self.assertEqual(mock.call_count, 2)

    def test_example_one(self):
        states = ['standing', 'walking', {'name': 'caffeinated'}]
        transitions = [['standing', 'walking', 'walk'],
                       ['walking', 'standing', 'stop'],
                       ['*', 'caffeinated', 'drink'],
                       ['caffeinated', 'standing', 'relax']]
        machine = Stuff.machine
        machine.add_states(states=states, initial='standing')
        machine.add_transitions(transitions)

        s = Stuff()
        s.dispatch(Event('walk'))
        s.dispatch(Event('stop'))
        s.dispatch(Event('drink'))
        self.assertEqual(s.state, 'caffeinated')
        with self.assertRaises(InvalidTransition):
            s.dispatch(Event('stop'))
        s.dispatch(Event('relax'))
        self.assertEqual(s.state, 'standing')
