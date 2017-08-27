import string as py_string
from collections import deque

from unittest import TestCase

from pysm import state_machine, State
from pysm.handler import add_states, add_switch_rules


class Initial(State):

    initial = True


class Number(State):
    pass


class Result(State):
    pass


@state_machine
class Calculator(object):

    def __init__(self):
        self.stack = deque()
        self.result = None

    def reset(self):
        self.stack.clear()
        self.result = None
        self.switch_to_initial()

    def calculate(self, string):
        self.reset()
        for char in string:
            self.parse(char)
            self.update_state()
        return self.result

    def parse(self, char):
        self.stack.append(char)

    def build_number(self):
        number1 = self.stack.pop()
        number2 = self.stack.pop()
        self.stack.append(number2 + number1)

    def do_operation(self):
        operation = self.stack.pop()
        y = self.stack.pop()
        x = self.stack.pop()
        # eval is evil
        self.stack.append(eval('float(%s) %s float(%s)' % (x, operation, y)))

    def do_equal(self):
        # '='
        self.stack.pop()
        self.result = self.stack.pop()

    def is_digit(self):
        return self.stack[-1] in py_string.digits

    def is_operator(self):
        return self.stack[-1] in '+-*/'

    def is_equal(self):
        return self.stack[-1] == '='

    def is_whitespace(self):
        return self.stack[-1] in py_string.whitespace

    def drop_whitespace(self):
        self.stack.pop()


add_states(Calculator, [Initial, Number, Result])

add_switch_rules(
    Calculator,
    {
        'Initial': [
            ('Number', 'is_digit'),
            ('Initial', 'is_operator', 'do_operation'),
            ('Result', 'is_equal', 'do_equal'),
            ('Initial', 'is_whitespace', 'drop_whitespace'),
        ],
        'Number': [
            ('Number', 'is_digit', 'build_number'),
            ('Initial', 'is_whitespace', 'drop_whitespace'),
        ],
    }
)


def test_calc_callbacks():
    calc = Calculator()
    for syntax, value in ((' 167 3 2 2 * * * 1 - =', 2003),
                          ('    167 3 2 2 * * * 1 - 2 / =', 1001.5),
                          ('    3   5 6 +  * =', 33),
                          ('        3    4       +     =', 7),
                          ('2 4 / 5 6 - * =', -0.5),):
        result = calc.calculate(syntax)
        assert result == value, (syntax, result, value)


class CalculatorTest(TestCase):

    def test_rpn(self):
        test_calc_callbacks()
