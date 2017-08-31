import string as py_string
from collections import deque
import operator

from unittest import TestCase

from pysm import Event, state_machine


@state_machine('calculator')
class Calculator(object):

    operators = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.div,
    }

    def __init__(self):
        self.stack = deque()
        self.result = None

    def reset(self):
        self.stack.clear()
        self.result = None
        self.machine.reinit_instance(self)

    def calculate(self, string):
        self.reset()
        for char in string:
            self.dispatch(Event('parse', input=char))
        return self.result

    def start_building_number(self, state, event):
        digit = event.input
        self.stack.append(int(digit))

    def build_number(self, state, event):
        digit = event.input
        number = str(self.stack.pop())
        number += digit
        self.stack.append(int(number))

    def do_operation(self, state, event):
        operation = event.input
        y = self.stack.pop()
        x = self.stack.pop()
        self.stack.append(self.operators[operation](float(x), float(y)))

    def do_equal(self, state, event):
        number = self.stack.pop()
        self.result = number


def is_digit(state, event):
    return event.input in py_string.digits


sm = Calculator.machine
sm.add_states(['initial', 'number', 'result'], initial='initial')

sm.add_transitions([
    {'from_state': 'initial', 'to_state': 'number', 'event': 'parse',
     'conditions': [is_digit], 'before': 'start_building_number'},
    {'from_state': 'number', 'to_state': 'number', 'event': 'parse',
     'conditions': [is_digit], 'before': 'build_number'},
    {'from_state': 'number', 'to_state': 'initial', 'event': 'parse',
     'conditions': [lambda state, evt: evt.input in py_string.whitespace]},
    {'from_state': 'initial', 'to_state': 'initial', 'event': 'parse',
     'conditions': [lambda state, evt: evt.input in '+-*/'],
     'before': 'do_operation'},
    {'from_state': 'initial', 'to_state': 'result', 'event': 'parse',
     'conditions': [lambda state, evt: evt.input == '='],
     'before': 'do_equal'},
])


def test_calc_callbacks():
    calc = Calculator()
    for syntax, value in ((' 167 3 2 2 * * * 1 - =', 2003),
                          ('    167 3 2 2 * * * 1 - 2 / =', 1001.5),
                          ('    3   5 6 +  * =', 33),
                          ('        3    4       +     =', 7),
                          ('2 4 / 5 6 - * =', -0.5),):
        result = calc.calculate(syntax)
        assert result == value, (syntax, result, value)
        calc.reset()


class CalculatorTest(TestCase):

    def test_rpn(self):
        test_calc_callbacks()
