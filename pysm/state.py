import inspect
from six import add_metaclass


class StateMeta(type):

    pysm_number = 0

    def __new__(cls, name, bases, attrs):
        cls = type.__new__(cls, name, bases, attrs)
        number = 0
        cls.state_methods = {}
        # check cython_function_or_method in str(type(value)) is a workaround
        for base in bases:
            number = number or getattr(base, 'pysm_number', 0)
            for name, value in base.__dict__.items():
                if (not name.startswith('__') and
                        inspect.isfunction(value) or
                        'cython_function_or_method' in str(type(value))):
                    cls.state_methods[name] = value
            for name, value in getattr(base, 'state_methods', {}).items():
                cls.state_methods[name] = value
        for name, value in attrs.items():
            if (not name.startswith('__') and
                    inspect.isfunction(value) or
                    'cython_function_or_method' in str(type(value))):
                cls.state_methods[name] = value
        if not number:
            number = StateMeta.pysm_number + 1
            StateMeta.pysm_number += 1
        cls.pysm_number = number
        return cls

    def __eq__(self, other):
        return (
            self is other or
            issubclass(self, other) or
            self is WhateverState or
            other is WhateverState
        )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.pysm_number

    def __unicode__(self):
        return self.__name__
    __repr__ = __str__ = __unicode__


@add_metaclass(StateMeta)
class State(object):

    def enter_state(self, from_state):
        pass

    def exit_state(self, to_state):
        pass

    def can_switch_state(self):
        return True


class WhateverState(State):
    pass
