import string as py_string

from pysm import Event, State, StateMachine


class Calculator(object):

    def __init__(self):
        self.result = None
        self.state_machine = self.get_state_machine()

    def get_state_machine(self):
        sm = StateMachine('calculator')
        initial = State('initial')
        number = State('number')
        sm.add_states([initial, number])
        sm.set_initial_state(initial)
        sm.add_transition(initial, number,
                          events=['parse'], inputs=py_string.digits,
                          action=self.start_building_number)
        sm.add_transition(number, None,
                          events=['parse'], inputs=py_string.digits,
                          action=self.build_number)
        sm.add_transition(number, initial,
                          events=['parse'], inputs=py_string.whitespace)
        sm.add_transition(initial, None,
                          events=['parse'], inputs='+-*/',
                          action=self.do_operation)
        sm.add_transition(initial, None,
                          events=['parse'], inputs='=',
                          action=self.do_equal)
        sm.initialize()
        return sm

    def calculate(self, string):
        state_machine = self.state_machine
        for char in string:
            state_machine.dispatch(Event('parse', input=char, entity=self))
        return self.result

    def start_building_number(self, event):
        digit = event.input
        self.state_machine.stack.append(int(digit))
        return True

    def build_number(self, event):
        digit = event.input
        number = str(self.state_machine.stack.pop())
        number += digit
        self.state_machine.stack.append(int(number))
        return True

    def do_operation(self, event):
        operation = event.input
        y = self.state_machine.stack.pop()
        x = self.state_machine.stack.pop()
        # eval is evil
        result = eval('float(%s) %s float(%s)' % (x, operation, y))
        self.state_machine.stack.append(result)
        return True

    def do_equal(self, event):
        number = self.state_machine.stack.pop()
        self.result = number
        return True


def test_calc_callbacks():
    calc = Calculator()
    assert calc.calculate(' 167 3 2 2 * * * 1 - =') == 2003
    assert calc.calculate('    167 3 2 2 * * * 1 - 2 / =') == 1001.5
    assert calc.calculate('    3   5 6 +  * =') == 33
    assert calc.calculate('        3    4       +     =') == 7
    assert calc.calculate('2 4 / 5 6 - * =') == -0.5


if __name__ == '__main__':
    test_calc_callbacks()
