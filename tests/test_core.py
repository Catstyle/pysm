# -*- coding: utf-8 -*-
from unittest import TestCase
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from pysm.core import Machine, State, Event, state_machine
from pysm import error


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

        with self.assertRaises(error.AlreadyHasInitialState):
            m.set_initial_state('C')
        m.set_initial_state('C', force=True)
        self.assertEqual(m.initial, 'C')

        with self.assertRaises(error.NoState):
            m.set_initial_state('X', force=True)

    def test_add_state(self):
        m = Stuff.machine
        self.assertDictEqual(m.states, {})

        states = ['A', 'B', {'name': 'C'}, 'D']
        m.add_states(states)
        self.assertTrue(len(m.states) == 4)

        with self.assertRaises(error.AlreadyHasState):
            m.add_state('A')

    def test_get_state(self):
        states = ['A', 'B', {'name': 'C'}, 'D']
        m = Stuff.machine
        m.add_states(states, initial='A', force=True)
        self.assertIsNotNone(m.get_state('A'))

        with self.assertRaises(error.NoState):
            m.get_state('X')

    def test_add_transition(self):
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
        self.assertEqual(len(m.transitions), 4)

        # Define with list of lists
        transitions = [
            ['A', 'B', 'walk'],
            ['B', 'C', 'run'],
            ['C', 'D', 'sprint']
        ]
        m._reset()
        m.add_states(states, initial='A')
        m.add_transitions(transitions)
        with self.assertRaises(error.NoState):
            m.add_transition('X', 'B', 'walk')

        with self.assertRaises(error.NoState):
            m.add_transition('A', 'X', 'walk')

    def test_dispatch(self):
        mock = MagicMock()

        def callback(state, event):
            mock()

        state = State('State1')
        state.handlers['advance'] = callback
        states = [state, 'State2', {'name': 'State3'}]
        transitions = [
            {'event': 'advance', 'from_state': 'State1', 'to_state': 'State2',
             'conditions': '!is_manager', 'after': callback},
            {'event': 'advance', 'from_state': 'State1', 'to_state': 'State3',
             'conditions': 'is_manager', 'after': 'on_advance'},
        ]
        m = Stuff.machine
        m.add_states(states)
        m.add_transitions(transitions)
        m.set_initial_state('State1')

        s = Stuff()
        s.is_manager = False
        s.dispatch(Event('advance'))
        self.assertEqual(s.state, 'State2')
        self.assertTrue(mock.called)
        self.assertEqual(mock.call_count, 2)

        s = Stuff()
        s.is_manager = True
        s.on_advance = callback
        s.dispatch(Event('advance'))
        self.assertEqual(s.state, 'State3')
        self.assertEqual(mock.call_count, 4)

    # def test_add_custom_state(self):
    #     s = self.stuff
    #     s.machine.add_states([{'name': 'E', 'children': ['1', '2', '3']}])
    #     s.machine.add_transition('go', '*', 'E%s1' % State.separator)
    #     s.machine.add_transition('run', 'E', 'C.3.a')
    #     s.go()
    #     s.run()

    def test_enter_exit_state(self):
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
        with self.assertRaises(error.InvalidTransition):
            s.dispatch(Event('stop'))
        s.dispatch(Event('relax'))
        self.assertEqual(s.state, 'standing')

    def test_switch_state(self):
        # private api
        states = ['A', 'B', 'C', 'D']
        transitions = [['A', 'C', 'go'], ['C', 'D', 'go']]

        m = Stuff.machine
        m.add_states(states=states, initial='A')
        m.add_transitions(transitions)

        s = Stuff()
        with self.assertRaises(error.InvalidTransition):
            s.dispatch(Event('run'))

        m._switch_state(s, 'B')
        self.assertEqual(s.state, 'B')
