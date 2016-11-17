from .error import HasNoState


class PysmEvent(object):

    def __init__(self, to_state):
        if to_state == 'WhateverState':
            raise ValueError('cannot use WhateverState as to_state')
        self.to_state = to_state


class Event(PysmEvent):

    def __get__(self, instance, owner):
        if not instance:
            return self

        def switch(*args, **kwargs):
            to_state = instance._pysm_states.get(self.to_state)
            if not to_state:
                raise HasNoState(self.to_state)
            switch_state(instance, to_state, *args, **kwargs)
        return switch

    def __str__(self):
        return u'pysm-event|%s' % self.name
    __unicode__ = __repr__ = __str__


class InstanceEvent(PysmEvent):

    def __init__(self, instance, to_state):
        super(InstanceEvent, self).__init__(to_state)
        self.instance = instance

    def __call__(self, *args, **kwargs):
        instance = self.instance
        to_state = instance._pysm_states.get(self.to_state)
        if not to_state:
            raise HasNoState(self.to_state)
        switch_state(instance, to_state, *args, **kwargs)

    def __str__(self):
        return u'pysm-instance-event|%s' % self.name
    __unicode__ = __repr__ = __str__


from .handler import switch_state  # noqa
