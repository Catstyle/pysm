from .error import InvalidTransition, HasNoState


class PysmEvent(object):

    def __init__(self, from_state, to_state, handler=lambda: True):
        self.from_state = from_state
        if to_state == 'WhateverState':
            raise ValueError('cannot use WhateverState as to_state')
        if not callable(handler) and not isinstance(handler, str):
            raise ValueError('handler should be callable')
        self.to_state = to_state
        self.handler = handler


class Event(PysmEvent):

    def __get__(self, instance, owner):
        if not instance:
            return self

        def switch(*args, **kwargs):
            current_state = instance.current_state
            current_name = current_state.__name__
            if (current_name != self.from_state and
                    self.from_state != 'WhateverState'):
                raise InvalidTransition(
                    '%s: calling `%s` from state `%s`, valid states `%s`' % (
                        instance, self.name, current_name, self.from_state
                    )
                )
            to_state = instance._pysm_states.get(self.to_state)
            if not to_state:
                raise HasNoState(self.to_state)
            switch_state(instance, current_state, to_state, *args, **kwargs)
        return switch

    def __str__(self):
        return u'pysm-event|%s' % self.name
    __unicode__ = __repr__ = __str__


class InstanceEvent(PysmEvent):

    def __init__(self, instance, from_state, to_state, handler=lambda: True):
        super(InstanceEvent, self).__init__(from_state, to_state, handler)
        self.instance = instance

    def __call__(self, *args, **kwargs):
        instance = self.instance
        current_state = instance.current_state
        current_name = current_state.__name__
        if (current_name not in self.from_state and
                self.from_state != ('WhateverState',)):
            raise InvalidTransition(
                '%s: calling `%s` from state `%s`, valid states `%s`' % (
                    instance, self.name, current_name, self.from_state
                )
            )
        to_state = instance._pysm_states.get(self.to_state)
        if not to_state:
            raise HasNoState(self.to_state)
        switch_state(instance, current_state, to_state, *args, **kwargs)

    def __str__(self):
        return u'pysm-instance-event|%s' % self.name
    __unicode__ = __repr__ = __str__


from .handler import switch_state  # noqa
