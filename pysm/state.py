import inspect
from six import add_metaclass, string_types


class StateMeta(type):

    def __new__(cls, name, bases, attrs):
        cls = type.__new__(cls, name, bases, attrs)
        cls.state_methods = {}
        for base in bases:
            for name, value in base.__dict__.items():
                if not name.startswith('__') and inspect.isfunction(value):
                    cls.state_methods[name] = value
        for name, value in attrs.items():
            if not name.startswith('__') and inspect.isfunction(value):
                cls.state_methods[name] = value
        return cls

    def __eq__(self, other):
        return self is other or self is WhateverState or other is WhateverState

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return id(self.__name__)

    def __unicode__(self):
        return self.__name__
    __str__ = __unicode__


@add_metaclass(StateMeta)
class State(object):

    def enter_state(self, from_state):
        pass

    def exit_state(self, to_state):
        pass

    def __eq__(self, other):
        if isinstance(other, string_types):
            return self.__class__.__name__ == other
        elif isinstance(other, State):
            return self.__class__ == other.__class__
        else:
            return NotImplemented

    def __ne__(self, other):
        return not self == other


class WhateverState(State):
    pass
